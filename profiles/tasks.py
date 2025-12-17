import time
import os
from io import BytesIO
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from .models import Resume, ResumeProcessingStatus
from .utils import extract_text_from_file

from .llm import create_extraction_chain

@shared_task
def process_resume_task(resume_id):
    try:
        resume = Resume.objects.get(id=resume_id)
        # Ensure status exists
        status_obj, created = ResumeProcessingStatus.objects.get_or_create(
            user=resume.user,
            defaults={'resume': resume, 'status': 'uploaded'}
        )
    except ObjectDoesNotExist:
        return "Resume not found"

    def update_status(new_status):
        status_obj.status = new_status
        status_obj.save(update_fields=['status', 'updated_at'])

    try:
        # Step 1: Extracting
        update_status('extracting')
        
        # Determine extension for extractor
        ext = os.path.splitext(resume.file.name)[1].lower()
        
        # Actual Extraction Logic
        with resume.file.open('rb') as f:
             file_content = f.read()
             file_stream = BytesIO(file_content)
             text = extract_text_from_file(file_stream, ext)
        
        resume.extracted_text = text
        resume.save()
        
        # Step 2: Extracted
        update_status('extracted')
        
        if not text:
            raise ValueError("No text extracted from resume")

        # Step 3: Analyzing (LLM Extraction)
        update_status('analyzing')
        
        chain = create_extraction_chain()
        structured_data = chain.invoke({"text": text})
        
        # Save to DB
        resume.structured_data = structured_data.model_dump()
        resume.save()

        # Step 4: Generated
        update_status('generated')

    except Exception as e:
        status_obj.status = 'failed'
        status_obj.error_message = str(e)
        status_obj.save(update_fields=['status', 'error_message', 'updated_at'])
        # Re-raise to let Celery know, or return string logic as below
        return f"Failed: {str(e)}"

    return "Completed"
