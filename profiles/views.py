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

        if not status_data:
            return Response({"error": "No resume found"}, status=status.HTTP_404_NOT_FOUND)

        current_status = status_data.status
        
        # Calculate progress
        status_map = {
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
        if current_status == 'review_required':
            message = "Please review extracted data and confirm to publish."
        elif current_status == 'failed':
            message = f"Processing failed: {status_data.error_message}"
        elif current_status == 'completed':
            message = "Portfolio ready to publish."
        else:
            message = "Processing resume..."

        return Response({
             "status": current_status,
             "progress": progress,
             "can_review": can_review,
             "can_edit": can_edit,
             "can_publish": can_publish,
             "message": message
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

        # Fetch structured_data
        resume_data = Resume.objects.filter(user=request.user).values('structured_data').first()

        if not resume_data or not resume_data['structured_data']:
             return Response({"error": "Structured data missing"}, status=status.HTTP_404_NOT_FOUND)

        return Response(resume_data['structured_data'])

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
            return Response({"error": "Validation failed", "details": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        # Save validated data
        final_data = validated_obj.model_dump()
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
