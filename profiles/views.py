import os
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Resume, ResumeProcessingStatus
from .serializers import ResumeSerializer
from .tasks import process_resume_task, requires_user_review, get_missing_portfolio_fields

class ResumeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        try:
            resume = Resume.objects.get(user=request.user)
            serializer = ResumeSerializer(resume)
            return Response(serializer.data)
        except Resume.DoesNotExist:
            return Response({"error": "No resume found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        # Check tier limit before allowing upload
        user = request.user
        if not user.can_process_resume():
            limit = user.get_resume_limit()
            return Response({
                "error": "Resume processing limit reached",
                "message": f"Your {user.get_user_tier_display()} tier allows {limit} resume processing. Please upgrade to continue.",
                "limit": limit,
                "used": user.resume_process_count,
                "tier": user.user_tier
            }, status=status.HTTP_403_FORBIDDEN)
        
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (e.g., 5MB)
        if file_obj.size > 5 * 1024 * 1024:
            return Response({"error": "File too large (max 5MB)"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type
        ext = os.path.splitext(file_obj.name)[1].lower()
        if ext not in ['.pdf', '.docx']:
             return Response({"error": "Unsupported file type. Use PDF or DOCX"}, status=status.HTTP_400_BAD_REQUEST)

        # Save Resume (Initialize)
        resume, created = Resume.objects.update_or_create(
            user=request.user,
            defaults={
                'original_filename': file_obj.name,
                'file': file_obj,
                'extracted_text': '' # Will be populated by task
            }
        )

        # Initialize Processing Status
        ResumeProcessingStatus.objects.update_or_create(
            user=request.user,
            defaults={
                'resume': resume,
                'status': 'uploaded',
                'error_message': None
            }
        )

        # Increment resume process count
        user.increment_resume_count()

        # Trigger Async Task
        process_resume_task.delay(resume.id)

        serializer = ResumeSerializer(resume)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ResumeStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        status_data = ResumeProcessingStatus.objects.filter(user=request.user).first()
        resume = Resume.objects.filter(user=request.user).first()

        current_status = status_data.status if status_data else 'not_uploaded'
        has_profile_photo = bool(resume.profile_photo) if resume else False
        
        # Calculate progress
        status_map = {
             'not_uploaded': 0,
             'uploaded': 10,
             'raw_extracting': 25,
             'raw_extracted': 40,
             'structure_extracting': 60,
             'structure_extracted': 80,
             'review_required': 90,
             'completed': 100,
             'failed': 0
        }
        progress = status_map.get(current_status, 0)
        
        can_review = current_status in ['structure_extracted', 'review_required', 'completed']
        # Edit is allowed in same states as review
        can_edit = can_review
        can_publish = current_status == 'completed'
        
        message = ""
        if current_status == 'not_uploaded':
             message = "Upload a resume to get started."
        elif current_status == 'review_required':
            message = "Please review extracted data and confirm to publish."
        elif current_status == 'failed':
            message = f"Processing failed: {status_data.error_message if status_data else 'Unknown error'}"
        elif current_status == 'completed':
            message = "Portfolio ready to publish."
        else:
            message = "Processing resume..."

        profile_photo_url = None
        if resume and resume.profile_photo:
            from .utils import get_absolute_media_url
            profile_photo_url = get_absolute_media_url(resume.profile_photo)

        return Response({
             "status": current_status,
             "progress": progress,
             "can_review": can_review,
             "can_edit": can_edit,
             "can_publish": can_publish,
             "message": message,
             "has_profile_photo": has_profile_photo,
             "profile_image_url": profile_photo_url
        })

class ResumeExtractedTextView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Fetch only the extracted_text field for the current user's resume
        # using values() to avoid loading the full model instance (single database query)
        resume_data = Resume.objects.filter(user=request.user).values('extracted_text').first()

        if not resume_data:
            return Response({"error": "No resume found"}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({"extracted_text": resume_data['extracted_text']})

from pydantic import ValidationError
from .schemas import PortfolioSchema

class PortfolioStructuredDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Guard: Check status first
        status_obj = ResumeProcessingStatus.objects.filter(user=request.user).values('status').first()
        if not status_obj:
             return Response({"error": "No resume found"}, status=status.HTTP_404_NOT_FOUND)
             
        allowed_states = ['structure_extracted', 'review_required', 'completed']
        if status_obj['status'] not in allowed_states:
             return Response(
                 {"error": "Processing not finished", "status": status_obj['status']}, 
                 status=status.HTTP_409_CONFLICT
             )

        # Fetch normalized Portfolio
        from .models import Portfolio
        from .serializers import PortfolioCompositionSerializer
        
        portfolio = Portfolio.objects.filter(user=request.user).first()
        if not portfolio:
             # Fallback if migration hasn't run or something failed, though tasks should ensure it.
             # Or return 404
             return Response({"error": "Portfolio not found"}, status=status.HTTP_404_NOT_FOUND)
             
        serializer = PortfolioCompositionSerializer(portfolio, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        try:
            resume = Resume.objects.get(user=request.user)
        except Resume.DoesNotExist:
            return Response({"error": "No resume found"}, status=status.HTTP_404_NOT_FOUND)

        current_data = resume.structured_data or {}
        incoming_data = request.data

    def patch(self, request):
        # Ensure Portfolio Exists
        from .models import Portfolio
        portfolio, _ = Portfolio.objects.get_or_create(user=request.user)

        # Use new update logic
        from .update_service import update_portfolio_from_json
        
        # We perform the update inside a transaction to ensure atomicity
        from django.db import transaction
        with transaction.atomic():
            update_portfolio_from_json(portfolio, request.data)
            
            # Also update status if needed
            status_obj, c = ResumeProcessingStatus.objects.get_or_create(user=request.user)
            # If we are editing, we are reviewing.
            if status_obj.status != 'completed':
                 status_obj.status = 'review_required'
                 status_obj.save()

        # Return the updated data using the GET serializer logic
        from .serializers import PortfolioCompositionSerializer
        # Refresh from db to get clean state
        portfolio.refresh_from_db()
        serializer = PortfolioCompositionSerializer(portfolio, context={'request': request})
        return Response(serializer.data)

class ConfirmPortfolioView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            resume = Resume.objects.get(user=request.user)
        except Resume.DoesNotExist:
            return Response({"error": "No resume found"}, status=status.HTTP_404_NOT_FOUND)
            
        status_obj = ResumeProcessingStatus.objects.get(resume=resume)
        
        # Check for missing fields before completing
        missing = get_missing_portfolio_fields(resume.structured_data)
        if missing:
             return Response({
                 "error": "Cannot complete portfolio. Missing fields.", 
                 "missing": missing
             }, status=status.HTTP_400_BAD_REQUEST)
             
        status_obj.status = 'completed'
        status_obj.save()
        
        return Response({"status": "completed"})

class PortfolioPublishStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        resume_data = Resume.objects.filter(user=request.user).values('structured_data').first()
        
        if not resume_data:
             return Response({"can_publish": False, "missing": ["resume"]}, status=status.HTTP_404_NOT_FOUND)
             
        data = resume_data['structured_data'] or {}
        missing = get_missing_portfolio_fields(data)
        
        return Response({
            "can_publish": len(missing) == 0,
            "missing": missing
        })

from django.db.models import Q
from .models import TechRegistry
from .serializers import TechRegistrySerializer
from .utils import download_and_process_icon

class TechSearchAPIView(APIView):
    permission_classes = [permissions.AllowAny] # Search should be public

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
             return Response({"error": "Query parameter 'q' is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Try exact match first (as-is, lowercased)
        code_name_exact = query.lower()
        
        # Also try normalized version (spaces to hyphens)
        code_name_normalized = query.lower().replace(' ', '-')
        
        # Try both variations
        tech = None
        try:
            # First try exact match
            tech = TechRegistry.objects.get(code_name=code_name_exact)
        except TechRegistry.DoesNotExist:
            # Then try normalized version
            try:
                tech = TechRegistry.objects.get(code_name=code_name_normalized)
            except TechRegistry.DoesNotExist:
                pass
        
        if tech:
            serializer = TechRegistrySerializer(tech)
            return Response(serializer.data)
        else:
            return Response({"error": f"Technology '{query}' not found"}, status=status.HTTP_404_NOT_FOUND)

class TechCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"TechCreate POST - Raw data: {request.data}")
        logger.info(f"TechCreate POST - Content-Type: {request.content_type}")
        logger.info(f"TechCreate POST - User: {request.user}")
        
        data = request.data.copy()
        
        # Support 'name' field as a convenience (user can send just 'name')
        if 'name' in data and 'display_name' not in data:
            data['display_name'] = data['name']
        
        # Handling icon URL processing if provided
        icon_url = data.get('icon_source_url') or data.get('icon_url') # Support both keys
        
        # Auto-generate code_name if not provided
        code_name = data.get('code_name', '').strip().lower().replace(' ', '-')
        
        # If user didn't provide code_name, derive from display_name
        if not code_name and 'display_name' in data:
             code_name = data['display_name'].strip().lower().replace(' ', '-')
        
        if not code_name:
            logger.error(f"TechCreate POST - Missing name/display_name/code_name. Data: {data}")
            return Response({"error": "Either 'name', 'display_name', or 'code_name' is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        data['code_name'] = code_name
        data['created_by_user'] = request.user.id
        
        # If code_name exists, return existing (or error?)
        # Let's return existing if found to avoid dupes
        if TechRegistry.objects.filter(code_name=code_name).exists():
             tech = TechRegistry.objects.get(code_name=code_name)
             logger.info(f"TechCreate POST - Tech already exists: {code_name}")
             return Response(TechRegistrySerializer(tech).data, status=status.HTTP_200_OK)

        serializer = TechRegistrySerializer(data=data)
        if serializer.is_valid():
             tech = serializer.save()
             logger.info(f"TechCreate POST - Created tech: {tech.display_name}")
             
             # Process Icon if URL provided and no file uploaded
             if icon_url and not 'icon_path' in request.FILES:
                  content_file, icon_type = download_and_process_icon(icon_url, code_name)
                  if content_file:
                       tech.icon_path.save(content_file.name, content_file, save=True)
                       tech.icon_type = icon_type
                       if 'icon_source_url' not in data:
                            tech.icon_source_url = icon_url
                       tech.save()
                       logger.info(f"TechCreate POST - Icon downloaded for: {code_name}")
             
             return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.error(f"TechCreate POST - Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.pagination import PageNumberPagination
from rest_framework import generics

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class TechListAPIView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = TechRegistry.objects.all().order_by('display_name')
    serializer_class = TechRegistrySerializer
    pagination_class = StandardResultsSetPagination
    search_fields = ['display_name', 'code_name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(display_name__icontains=query) | Q(code_name__icontains=query)
            )
        return queryset

from .models import SocialRegistry
from .serializers import SocialRegistrySerializer

class SocialSearchAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
             return Response({"error": "Query parameter 'q' is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize: lowercase, replace spaces with hyphens
        code_name_exact = query.lower()
        code_name_normalized = query.lower().replace(' ', '-')
        
        # Try both variations
        social = None
        try:
            social = SocialRegistry.objects.get(code_name=code_name_exact)
        except SocialRegistry.DoesNotExist:
            try:
                social = SocialRegistry.objects.get(code_name=code_name_normalized)
            except SocialRegistry.DoesNotExist:
                pass
        
        if social:
            serializer = SocialRegistrySerializer(social)
            return Response(serializer.data)
        else:
            return Response({"error": f"Social platform '{query}' not found"}, status=status.HTTP_404_NOT_FOUND)

class SocialListAPIView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = SocialRegistry.objects.all().order_by('display_name')
    serializer_class = SocialRegistrySerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(display_name__icontains=query) | Q(code_name__icontains=query)
            )
        return queryset

class SocialCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"SocialCreate POST - Raw data: {request.data}")
        
        data = request.data.copy()
        
        # Support 'name' field as a convenience
        if 'name' in data and 'display_name' not in data:
            data['display_name'] = data['name']
        
        # Handling icon URL processing if provided
        icon_url = data.get('icon_source_url') or data.get('icon_url')
        
        # Auto-generate code_name if not provided
        code_name = data.get('code_name', '').strip().lower().replace(' ', '-')
        
        if not code_name and 'display_name' in data:
             code_name = data['display_name'].strip().lower().replace(' ', '-')
        
        if not code_name:
            logger.error(f"SocialCreate POST - Missing name/display_name/code_name. Data: {data}")
            return Response({"error": "Either 'name', 'display_name', or 'code_name' is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        data['code_name'] = code_name
        data['created_by_user'] = request.user.id
        
        # If code_name exists, return existing
        if SocialRegistry.objects.filter(code_name=code_name).exists():
             social = SocialRegistry.objects.get(code_name=code_name)
             logger.info(f"SocialCreate POST - Social already exists: {code_name}")
             return Response(SocialRegistrySerializer(social).data, status=status.HTTP_200_OK)

        serializer = SocialRegistrySerializer(data=data)
        if serializer.is_valid():
             social = serializer.save()
             logger.info(f"SocialCreate POST - Created social: {social.display_name}")
             
             # Process Icon if URL provided
             if icon_url and not 'icon_path' in request.FILES:
                  content_file, icon_type = download_and_process_icon(icon_url, code_name)
                  if content_file:
                       social.icon_path.save(content_file.name, content_file, save=True)
                       social.icon_type = icon_type
                       if 'icon_source_url' not in data:
                            social.icon_source_url = icon_url
                       social.save()
                       logger.info(f"SocialCreate POST - Icon downloaded for: {code_name}")
             
             return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.error(f"SocialCreate POST - Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfilePhotoUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        if 'profile_photo' not in request.FILES:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['profile_photo']
        resume = Resume.objects.filter(user=request.user).first()
        if not resume:
             return Response({"error": "Resume profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        resume.profile_photo = file
        resume.save()
        
        from .utils import get_absolute_media_url
        photo_url = get_absolute_media_url(resume.profile_photo)
        
        # Update structured data immediately
        if not resume.structured_data:
            resume.structured_data = {}
        if 'hero' not in resume.structured_data:
            resume.structured_data['hero'] = {}
            
        resume.structured_data['hero']['profile_image'] = photo_url
        resume.save()

        return Response({"profile_image": photo_url}, status=status.HTTP_200_OK)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import CompanyRegistry
from .serializers import CompanyRegistrySerializer

class CompanyLogoUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Upload a company logo file.
        Saves to user's PortfolioExperience.logo (user-scoped), NOT the shared CompanyRegistry.
        Expects: company_name (string) and logo (file)
        """
        from .models import Portfolio, PortfolioExperience
        from .utils import get_absolute_media_url
        from django.core.files.base import ContentFile
        import re
        import uuid
        
        company_name = request.data.get('company_name')
        logo_file = request.FILES.get('logo')
        
        if not company_name:
            return Response(
                {"error": "company_name is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not logo_file:
            return Response(
                {"error": "logo file is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find user's portfolio
        portfolio = Portfolio.objects.filter(user=request.user).first()
        if not portfolio:
            return Response(
                {"error": "Portfolio not found. Please upload a resume first."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Find the experience entry for this company (case-insensitive)
        experience = PortfolioExperience.objects.filter(
            portfolio=portfolio,
            company_name__iexact=company_name
        ).first()
        
        if not experience:
            return Response(
                {"error": f"No experience found for company '{company_name}'"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Sanitize filename to prevent SuspiciousFileOperation errors
        original_name = logo_file.name
        
        # Get extension
        ext = os.path.splitext(original_name)[1].lower()
        if not ext:
            ext = '.png'  # Default extension
        
        # Sanitize company name for filename (remove special chars, limit length)
        safe_company = re.sub(r'[^\w\s-]', '', company_name)[:30].strip().replace(' ', '_').lower()
        
        # Generate a clean, short filename
        short_id = uuid.uuid4().hex[:8]
        sanitized_name = f"{safe_company}_{short_id}{ext}"
        
        # Ensure it's not too long (max ~50 chars for safety)
        if len(sanitized_name) > 50:
            sanitized_name = f"logo_{short_id}{ext}"
        
        # Rename the file
        logo_file.name = sanitized_name
        
        # Save the logo to user's experience (NOT the shared CompanyRegistry)
        experience.logo = logo_file
        experience.save(update_fields=['logo'])
        
        # Return the logo URL
        logo_url = get_absolute_media_url(experience.logo)
        
        return Response({
            "company_name": experience.company_name,
            "logo_url": logo_url
        }, status=status.HTTP_200_OK)

