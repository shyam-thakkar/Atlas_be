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
             profile_photo_url = request.build_absolute_uri(resume.profile_photo.url)

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

        # Fetch full resume object
        resume = Resume.objects.filter(user=request.user).first()
        if not resume:
             return Response({"error": "No resume found"}, status=status.HTTP_404_NOT_FOUND)

        if not resume.structured_data:
             return Response({"error": "Structured data missing"}, status=status.HTTP_404_NOT_FOUND)
             
        data = resume.structured_data
        
        # Inject profile_photo URL if available
        if resume.profile_photo:
            try:
                photo_url = request.build_absolute_uri(resume.profile_photo.url)
                if 'hero' not in data:
                    data['hero'] = {}
                data['hero']['profile_image'] = photo_url
            except Exception:
                pass # Fail silently if file issue

        return Response(data)

    def patch(self, request):
        try:
            resume = Resume.objects.get(user=request.user)
        except Resume.DoesNotExist:
            return Response({"error": "No resume found"}, status=status.HTTP_404_NOT_FOUND)

        current_data = resume.structured_data or {}
        incoming_data = request.data

        # Helper for recursive merge
        def deep_merge(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    deep_merge(target[key], value)
                else:
                    target[key] = value
            return target

        # Merge updates
        updated_data = deep_merge(current_data.copy(), incoming_data)

        # Validate with Pydantic
        try:
            validated_obj = PortfolioSchema(**updated_data)
        except ValidationError as e:
            # Format errors to be JSON serializable
            error_details = []
            for error in e.errors():
                error_details.append({
                    'field': ' -> '.join(str(loc) for loc in error['loc']),
                    'message': str(error['msg']),
                    'type': error['type']
                })
            return Response({
                "error": "Validation failed", 
                "details": error_details
            }, status=status.HTTP_400_BAD_REQUEST)

        # Save validated data (include extra fields like dynamic socials)
        final_data = validated_obj.model_dump(mode='json', exclude_none=False)
        
        # Clean tech_stack: remove {{}} if present
        if 'tech_stack' in final_data and isinstance(final_data['tech_stack'], list):
            cleaned_tech_stack = []
            for tech in final_data['tech_stack']:
                cleaned = tech.strip()
                if cleaned.startswith('{{') and cleaned.endswith('}}'):
                    cleaned = cleaned[2:-2].strip()
                cleaned_tech_stack.append(cleaned)
            final_data['tech_stack'] = cleaned_tech_stack
        
        resume.structured_data = final_data
        resume.save()
        
        # Post-save: Ensure status is review_required (user must explicitly confirm completion)
        # Even if data is valid, we don't auto-complete anymore.
        status_obj = ResumeProcessingStatus.objects.get(resume=resume)
        if status_obj.status != 'completed': # Don't revert if already completed? Or maybe we DO?
             # User requested: "once user send any data in structured it is savd and one confirm api which makes the data to complete"
             # So saving keeps it in 'review_required' until confirmed.
             status_obj.status = 'review_required'
             status_obj.save()

        return Response(resume.structured_data)

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
        
        photo_url = request.build_absolute_uri(resume.profile_photo.url)
        
        # Update structured data immediately
        if not resume.structured_data:
            resume.structured_data = {}
        if 'hero' not in resume.structured_data:
            resume.structured_data['hero'] = {}
            
        resume.structured_data['hero']['profile_image'] = photo_url
        resume.save()

        return Response({"profile_image": photo_url}, status=status.HTTP_200_OK)
