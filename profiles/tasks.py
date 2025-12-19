import time
import os
from io import BytesIO
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from .models import Resume, ResumeProcessingStatus
from .utils import extract_text_from_file

from .llm import create_extraction_chain

def get_missing_portfolio_fields(data) -> list:
    """
    Returns a list of missing critical fields for the completion portfolio.
    """
    return []

def requires_user_review(data) -> bool:
    return bool(len(get_missing_portfolio_fields(data)) > 0)

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

        # Step 1: Raw Extracting
        update_status('raw_extracting')
        
        # Determine extension for extractor
        ext = os.path.splitext(resume.file.name)[1].lower()
        
        # Actual Extraction Logic
        with resume.file.open('rb') as f:
             file_content = f.read()
             file_stream = BytesIO(file_content)
             text = extract_text_from_file(file_stream, ext)
        
        resume.extracted_text = text
        resume.save()
        
        # Step 2: Raw Extracted
        update_status('raw_extracted')
        
        if not text:
            raise ValueError("No text extracted from resume")

        # Step 3: Structure Extracting (LLM)
        update_status('structure_extracting')
        
        chain = create_extraction_chain()
        structured_data = chain.invoke({"text": text})
        
        # Save to DB
        data_dict = structured_data.model_dump()
        
        # Clean tech_stack: remove {{}} if LLM accidentally added them
        if 'tech_stack' in data_dict and isinstance(data_dict['tech_stack'], list):
            cleaned_tech_stack = []
            for tech in data_dict['tech_stack']:
                # Remove {{ and }} if present
                cleaned = tech.strip()
                if cleaned.startswith('{{') and cleaned.endswith('}}'):
                    cleaned = cleaned[2:-2].strip()
                cleaned_tech_stack.append(cleaned)
            data_dict['tech_stack'] = cleaned_tech_stack
        
        resume.structured_data = data_dict
        resume.save()

        # --- NEW HYBRID PIPELINE ---
        from .models import Portfolio, PortfolioAISnapshot
        from .services import normalize_snapshot_service

        # 1. Ensure Portfolio Exists
        portfolio, _ = Portfolio.objects.get_or_create(
            user=resume.user,
            defaults={'title': f"{resume.user.name or 'User'}'s Portfolio"}
        )

        # 2. Create AI Snapshot
        snapshot = PortfolioAISnapshot.objects.create(
            portfolio=portfolio,
            raw_resume_text=text,
            extracted_jsonb=data_dict,
            model_name="gemini-2.0-flash-exp"
        )

        # 3. Normalize Data
        normalize_snapshot_service(portfolio, snapshot)
        # ---------------------------

        # Step 4: Structure Extracted
        update_status('structure_extracted')
        
        # Step 5: Review Required (Wait for User Confirmation)
        # Even if perfect, we want explicit confirmation.
        update_status('review_required')

    except Exception as e:
        status_obj.status = 'failed'
        status_obj.error_message = str(e)
        status_obj.save(update_fields=['status', 'error_message', 'updated_at'])
        # Re-raise to let Celery know, or return string logic as below
        return f"Failed: {str(e)}"

    return "Completed"


