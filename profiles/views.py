import os
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Resume, ResumeProcessingStatus
from .serializers import ResumeSerializer
from .tasks import process_resume_task

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
        # Optimized query: Fetch only 'status' field using the index on 'user'
        # values() ensures we don't load the model instance, just the dict
        status_data = ResumeProcessingStatus.objects.filter(user=request.user).values('status').first()

        if not status_data:
            return Response({"error": "No resume found"}, status=status.HTTP_404_NOT_FOUND)

        current_status = status_data['status']
        etag = f'"{current_status}"'

        # ETag Check for 304 Not Modified
        if_none_match = request.META.get('HTTP_IF_NONE_MATCH')
        if if_none_match == etag:
            return Response(status=status.HTTP_304_NOT_MODIFIED)

        response = Response({"status": current_status})
        response['ETag'] = etag
        return response

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
        # Fetch only the structured_data field for the current user's resume
        # optimized single query
        resume_data = Resume.objects.filter(user=request.user).values('structured_data').first()

        if not resume_data:
             return Response({"error": "No resume found"}, status=status.HTTP_404_NOT_FOUND)

        if not resume_data['structured_data']:
             return Response({"error": "Structured data not generated yet"}, status=status.HTTP_404_NOT_FOUND)

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
        resume.structured_data = validated_obj.model_dump()
        resume.save()

        return Response(resume.structured_data)
