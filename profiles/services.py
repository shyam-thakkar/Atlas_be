
from django.db import transaction
from django.core.files.base import ContentFile
from .models import (
    Portfolio, PortfolioAISnapshot, PortfolioProfile, PortfolioTech, 
    PortfolioExperience, PortfolioProject, PortfolioEducation, PortfolioSocial,
    TechRegistry, SocialRegistry, Media, CompanyRegistry
)
from datetime import datetime
import requests
from django.core.files.base import ContentFile
from urllib.parse import urlparse
import os
from .utils import normalize_url

def download_logo_from_url(url):
    """
    Downloads a logo from URL and returns a ContentFile ready to save to ImageField.
    Returns None if download fails.
    """
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        # Get filename from URL or generate one
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path) or 'logo.png'
        
        # Ensure proper extension
        if not any(filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.svg', '.webp']):
            # Try to detect from content-type
            content_type = response.headers.get('content-type', '')
            if 'png' in content_type:
                filename += '.png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                filename += '.jpg'
            elif 'svg' in content_type:
                filename += '.svg'
            else:
                filename += '.png'  # default
        
        return ContentFile(response.content, name=filename)
    except Exception as e:
        print(f"Failed to download logo from {url}: {e}")
        return None


def normalize_date(date_str):
    """
    Helper to parse fuzzy dates like 'Present', '2023', 'Jan 2023', '2023-01-01', 'June 2025'
    Returns a python date object or None.
    """
    if not date_str:
        return None
    
    s = str(date_str).strip()
    if s.lower() == 'present':
        return None  # Current position implies no end date usually

    formats = [
        "%Y-%m-%d",       # 2023-01-01
        "%Y-%m",          # 2023-01
        "%B %Y",          # June 2025
        "%b %Y",          # Dec 2024
        "%Y",             # 2023
        "%d/%m/%Y",       # 01/01/2023
    ]

    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except (ValueError, TypeError):
            continue
            
    return None

@transaction.atomic
def normalize_snapshot_service(portfolio, snapshot):
    """
    Takes a PortfolioAISnapshot and populates the normalized Portfolio tables.
    This is an IDEMPOTENT operation (clears previous data for this portfolio to avoid duplication).
    """
    data = snapshot.extracted_jsonb
    
    # 2. Portfolio Profile
    PortfolioProfile.objects.filter(portfolio=portfolio).delete()
    
    hero_section = data.get('hero', {})
    about_section = data.get('about', {})
    
    headline = hero_section.get('headline') or ''
    short_bio = hero_section.get('short_bio') or hero_section.get('sub_heading', '')
    long_bio = about_section.get('long_bio') or about_section.get('description', '')
    
    # Update User's Name if present
    full_name = hero_section.get('full_name')
    if full_name:
        user = portfolio.user
        user.name = full_name
        user.save(update_fields=['name'])
    
    PortfolioProfile.objects.create(
        portfolio=portfolio,
        headline=headline,
        short_bio=short_bio,
        long_bio=long_bio
    )
    
    # 3. Tech Stack
    PortfolioTech.objects.filter(portfolio=portfolio).delete()
    
    tech_stack_list = data.get('tech_stack', [])
    missing_techs = []
    
    for idx, tech_name in enumerate(tech_stack_list):
        cleaned_name = tech_name.replace("{{", "").replace("}}", "").strip()
        if not cleaned_name: continue
        
        code_name = cleaned_name.lower().replace(" ", "-")
        
        # Find or Create in Registry
        tech_entry = TechRegistry.objects.filter(code_name=code_name).first()
        if not tech_entry:
            tech_entry = TechRegistry.objects.filter(display_name__iexact=cleaned_name).first()
        
        if tech_entry:
            PortfolioTech.objects.create(
                portfolio=portfolio,
                tech=tech_entry,
                display_order=idx
            )
        else:
             # Add to missing list
             missing_techs.append(cleaned_name)
    
    # Save missing techs to portfolio
    portfolio.missing_tech_stack = missing_techs
    portfolio.save(update_fields=['missing_tech_stack'])

    # 4. Experience
    PortfolioExperience.objects.filter(portfolio=portfolio).delete()
    
    experience_list = data.get('experience', [])
    for exp in experience_list:
        start_date = normalize_date(exp.get('start_date'))
        end_date = normalize_date(exp.get('end_date'))
        
        # Check explicit strict 'Present' or if end_date remains None while start_date is set?
        # Actually user logic: "June 2025 - Present" -> end_date is None, is_current=True
        is_current = str(exp.get('end_date', '')).lower() == 'present'
        
        company_name = exp.get('company', 'Unknown')
        
        # Company Registry Logic
        company_reg = None
        if company_name and company_name != 'Unknown':
            # normalize name for search
            company_reg = CompanyRegistry.objects.filter(name__iexact=company_name).first()
            # If not found, we DO NOT create it automatically per user request.
            
            # If linked and input has logo_url, download and save as file
            if company_reg:
                input_logo = exp.get('logo') or exp.get('logo_url')
                if input_logo and not company_reg.logo_file:
                    # If it's a URL, download it
                    if isinstance(input_logo, str) and input_logo.startswith('http'):
                        logo_file = download_logo_from_url(input_logo)
                        if logo_file:
                            company_reg.logo_file.save(logo_file.name, logo_file, save=True)
                    # If it's already a file object (from upload), save directly
                    elif hasattr(input_logo, 'read'):
                        company_reg.logo_file = input_logo
                        company_reg.save(update_fields=['logo_file'])

        PortfolioExperience.objects.create(
            portfolio=portfolio,
            company=company_reg, # Link registry if exists
            company_name=company_name, 
            role=exp.get('role', 'Unknown'),
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=exp.get('summary', '') 
        )

    # 5. Projects
    PortfolioProject.objects.filter(portfolio=portfolio).delete()
    
    projects_list = data.get('projects', [])
    for idx, proj in enumerate(projects_list):
        project_obj = PortfolioProject.objects.create(
            portfolio=portfolio,
            title=proj.get('name', 'Untitled'),
            description=proj.get('description', ''),
            repo_url=normalize_url(proj.get('github_link', '')),
            live_url=normalize_url(proj.get('live_link', '')),
            key_features=proj.get('key_features', []),
            technical_challenges=proj.get('technical_challenges', []),
            year=proj.get('year', ''),
            project_type=proj.get('project_type', ''),
            display_order=idx
        )
        
        # Link tech used and track missing ones
        proj_techs = proj.get('technologies', [])
        missing_proj_techs = []
        if proj_techs:
            for t_name in proj_techs:
                t_clean = t_name.replace("{{", "").replace("}}", "").strip()
                if not t_clean: continue
                
                t_code = t_clean.lower().replace(" ", "")
                t_reg = TechRegistry.objects.filter(code_name=t_code).first()
                if t_reg:
                     project_obj.tech_used.add(t_reg)
                else:
                    # Add to missing list
                    missing_proj_techs.append(t_clean)
        
        # Save missing techs to project
        project_obj.missing_technologies = missing_proj_techs
        project_obj.save(update_fields=['missing_technologies'])
        
        # Handle thumbnail - download if URL provided
        thumbnail_input = proj.get('thumbnail') or proj.get('thumbnail_url')
        if thumbnail_input and not project_obj.thumbnail:
            # If it's a URL, download it
            if isinstance(thumbnail_input, str) and thumbnail_input.startswith('http'):
                thumbnail_file = download_logo_from_url(thumbnail_input)
                if thumbnail_file:
                    project_obj.thumbnail.save(thumbnail_file.name, thumbnail_file, save=True)
            # If it's already a file object, save directly
            elif hasattr(thumbnail_input, 'read'):
                project_obj.thumbnail = thumbnail_input
                project_obj.save(update_fields=['thumbnail'])

    # 6. Education
    PortfolioEducation.objects.filter(portfolio=portfolio).delete()
    education_list = data.get('education', [])
    for edu in education_list:
        # Handle both date formats: full date or just year
        start = edu.get('start_date') or edu.get('start_year')
        end = edu.get('end_date') or edu.get('end_year')
        
        # Normalize grade_type to lowercase
        grade_type = (edu.get('grade_type') or '').lower().strip()
        valid_types = ['cgpa', 'sgpa', 'percentage', 'gpa', 'other']
        if grade_type not in valid_types:
            # Try to infer from grade value
            grade_val = edu.get('grade', '')
            if '%' in str(grade_val):
                grade_type = 'percentage'
            elif grade_val:
                grade_type = 'cgpa'  # Default assumption for numeric grades
        
        PortfolioEducation.objects.create(
            portfolio=portfolio,
            institution=edu.get('institution', ''),
            degree=edu.get('degree', ''),
            field_of_study=edu.get('field_of_study', '') or edu.get('major', ''),
            grade=edu.get('grade', ''),
            grade_type=grade_type,
            start_date=normalize_date(start),
            end_date=normalize_date(end),
            description=edu.get('description', '')
        )

    # 7. Socials
    PortfolioSocial.objects.filter(portfolio=portfolio).delete()
    socials = data.get('socials', {}) # Key is 'socials'
    
    if isinstance(socials, dict):
        for platform_name, url in socials.items():
            if not url: continue
            
            p_code = platform_name.lower().replace(" ", "-")
            
            social_reg = SocialRegistry.objects.filter(code_name=p_code).first()
            if social_reg:
                PortfolioSocial.objects.create(
                    portfolio=portfolio,
                    social_platform=social_reg,
                    url=normalize_url(url)
                )
    
    # 8. Contact Section - Initialize with empty/default values
    # This creates an empty contact section that users can edit later
    if not portfolio.contact_data:
        portfolio.contact_data = {
            'message': '',
            'cta_text': ''
        }
        portfolio.save(update_fields=['contact_data'])
    
    return True

