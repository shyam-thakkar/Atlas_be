
from .models import (
    Portfolio, PortfolioProfile, PortfolioTech, PortfolioExperience, 
    PortfolioProject, PortfolioEducation, PortfolioSocial, TechRegistry, SocialRegistry,
    CompanyRegistry
)
from .utils import normalize_url

def update_portfolio_from_json(portfolio, data):
    """
    Updates the normalized Portfolio tables from a JSON dictionary (full or partial).
    This logic mirrors the normalization service but handles updates intelligently.
    """
    
    # 1. Update Profile (Hero/About)
    profile = getattr(portfolio, 'profile', None)
    if not profile:
        profile = PortfolioProfile.objects.create(portfolio=portfolio)
        
    # Helper to check if key exists in data to allow partial updates (if user sends only hero, don't wipe about)
    # However, the frontend usually sends the FULL object back or structure specific patches.
    # The view layer logic we're replacing did a "Deep Merge" then "Replace".
    # Here, if we receive "hero", we update hero fields.
    
    if 'hero' in data:
        hero = data['hero']
        # headline, short_bio
        if 'headline' in hero: profile.headline = hero['headline']
        if 'short_bio' in hero: profile.short_bio = hero['short_bio']
        
        # Update User Name
        if 'full_name' in hero and hero['full_name']:
            user = portfolio.user
            user.name = hero['full_name']
            user.save(update_fields=['name'])
    
    if 'about' in data:
        about = data['about']
        if 'long_bio' in about: profile.long_bio = about['long_bio']
        
    profile.save()

    # NOTE: For list fields (Experience, Projects, Tech, Socials), 
    # it is hard to do "partial updates" (insert/update/delete) without IDs.
    # The safest strategy for this MVP is: 
    # IF the key exists in data, WIPE and REWRITE that specific section.
    
    # 2. Tech Stack
    if 'tech_stack' in data:
        PortfolioTech.objects.filter(portfolio=portfolio).delete()
        missing_techs = []
        for idx, tech_name in enumerate(data['tech_stack']):
            cleaned = tech_name.strip()
            if not cleaned: continue
            
            # Remove {{}}
            if cleaned.startswith('{{') and cleaned.endswith('}}'):
                cleaned = cleaned[2:-2].strip()
                
            code = cleaned.lower().replace(' ', '-')
            
            # Find/Create
            tech = TechRegistry.objects.filter(code_name=code).first()
            if not tech:
                tech = TechRegistry.objects.filter(display_name__iexact=cleaned).first()
            if tech:
                PortfolioTech.objects.create(portfolio=portfolio, tech=tech, display_order=idx)
            else:
                 missing_techs.append(cleaned)
        
        portfolio.missing_tech_stack = missing_techs
        portfolio.save(update_fields=['missing_tech_stack'])

    # 3. Experience
    if 'experience' in data:
        PortfolioExperience.objects.filter(portfolio=portfolio).delete()
        from .services import normalize_date, download_logo_from_url
        
        for exp in data['experience']:
             company_name = exp.get('company_name', '') or exp.get('company', '')
             
             # Company Registry Logic - lookup only, NO WRITES to shared registry
             company_reg = None
             if company_name:
                 company_reg = CompanyRegistry.objects.filter(name__iexact=company_name).first()
                 # If not found, do NOT create. User can still have the experience with company_name text.

             # Create the experience record
             experience_obj = PortfolioExperience.objects.create(
                portfolio=portfolio,
                company=company_reg,
                company_name=company_name,
                role=exp.get('role', ''),
                start_date=normalize_date(exp.get('start_date')),
                end_date=normalize_date(exp.get('end_date')),
                is_current=exp.get('is_current') or (str(exp.get('end_date', '')).lower() == 'present'),
                description=exp.get('description') or exp.get('summary', '')
             )
             
             # Handle logo - save to USER's experience, NOT the shared CompanyRegistry
             input_logo = exp.get('logo') or exp.get('logo_url')
             if input_logo:
                 # If it's a URL, download it
                 if isinstance(input_logo, str) and input_logo.startswith('http'):
                     logo_file = download_logo_from_url(input_logo)
                     if logo_file:
                         experience_obj.logo.save(logo_file.name, logo_file, save=True)
                 # If it's already a file object (from upload), save directly
                 elif hasattr(input_logo, 'read'):
                     experience_obj.logo = input_logo
                     experience_obj.save(update_fields=['logo'])

    # 4. Projects
    if 'projects' in data:
        PortfolioProject.objects.filter(portfolio=portfolio).delete()
        for idx, proj in enumerate(data['projects']):
            p_obj = PortfolioProject.objects.create(
                portfolio=portfolio,
                title=proj.get('title') or proj.get('name', ''),
                description=proj.get('description', ''),
                repo_url=normalize_url(proj.get('repo_url') or proj.get('github_link', '')),
                live_url=normalize_url(proj.get('live_url') or proj.get('live_link', '')),
                key_features=proj.get('key_features', []),
                technical_challenges=proj.get('technical_challenges', []),
                year=proj.get('year', ''),
                project_type=proj.get('project_type', ''),
                display_order=idx
            )
            # Tech Used - track missing ones
            # Frontend often sends 'technologies': ['python', 'django']
            techs = proj.get('technologies', []) or proj.get('tech_stack', [])
            missing_proj_techs = []
            for t_name in techs:
                cleaned = t_name.strip()
                if cleaned.startswith('{{') and cleaned.endswith('}}'):
                     cleaned = cleaned[2:-2].strip()
                if not cleaned: continue
                c_code = cleaned.lower().replace(' ', '-')
                
                t_reg = TechRegistry.objects.filter(code_name=c_code).first()
                if t_reg:
                    p_obj.tech_used.add(t_reg)
                else:
                    # Add to missing list
                    missing_proj_techs.append(cleaned)
            
            # Save missing techs to project
            p_obj.missing_technologies = missing_proj_techs
            p_obj.save(update_fields=['missing_technologies'])
            
            # Handle thumbnail - download if URL provided
            thumbnail_input = proj.get('thumbnail') or proj.get('thumbnail_url')
            if thumbnail_input and not p_obj.thumbnail:
                from .services import download_logo_from_url
                
                # If it's a URL, download it
                if isinstance(thumbnail_input, str) and thumbnail_input.startswith('http'):
                    thumbnail_file = download_logo_from_url(thumbnail_input)
                    if thumbnail_file:
                        p_obj.thumbnail.save(thumbnail_file.name, thumbnail_file, save=True)
                # If it's already a file object (from upload), save directly
                elif hasattr(thumbnail_input, 'read'):
                    p_obj.thumbnail = thumbnail_input
                    p_obj.save(update_fields=['thumbnail'])

    # 5. Education
    if 'education' in data:
        PortfolioEducation.objects.filter(portfolio=portfolio).delete()
        from .services import normalize_date
        for edu in data['education']:
            # Handle both date formats: full date or just year
            start = edu.get('start_date') or edu.get('start_year')
            end = edu.get('end_date') or edu.get('end_year')
            
            # Normalize grade_type to lowercase
            grade_type = (edu.get('grade_type') or '').lower().strip()
            valid_types = ['cgpa', 'sgpa', 'percentage', 'gpa', 'other']
            if grade_type not in valid_types:
                # Try to infer from grade value
                grade_val = edu.get('grade', '')
                if '%' in grade_val:
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
            
    # 6. Socials
    if 'socials' in data:
        PortfolioSocial.objects.filter(portfolio=portfolio).delete()
        socials = data['socials']
        # Handle dict format: {"github": "url"}
        if isinstance(socials, dict):
            for key, val in socials.items():
                if not val: continue
                code = key.lower().replace(' ', '-')
                s_reg = SocialRegistry.objects.filter(code_name=code).first()
                if s_reg:
                    PortfolioSocial.objects.create(portfolio=portfolio, social_platform=s_reg, url=normalize_url(val))

    # 7. Contact Section
    if 'contact' in data:
        contact = data['contact']
        if isinstance(contact, dict):
            # Merge with existing contact_data to allow partial updates
            current_contact = portfolio.contact_data or {}
            if 'message' in contact:
                current_contact['message'] = contact['message']
            if 'cta_text' in contact:
                current_contact['cta_text'] = contact['cta_text']
            portfolio.contact_data = current_contact
            portfolio.save(update_fields=['contact_data'])

