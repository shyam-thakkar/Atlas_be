from rest_framework import serializers
from .models import Resume, TechRegistry, SocialRegistry

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ('id', 'original_filename', 'uploaded_at', 'file')
        read_only_fields = ('id', 'original_filename', 'uploaded_at', 'file')

class TechRegistrySerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TechRegistry
        fields = [
            'id', 'display_name', 'code_name', 'icon_type', 
            'icon_path', 'icon_url', 'icon_source_url', 'doc_url', 
            'color_variant', 'is_verified'
        ]
        read_only_fields = ['id', 'is_verified', 'icon_path']
    
    def get_icon_url(self, obj):
        from .utils import get_absolute_media_url
        return get_absolute_media_url(obj.icon_path)

class SocialRegistrySerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SocialRegistry
        fields = [
            'id', 'display_name', 'code_name', 'icon_type',
            'icon_path', 'icon_url', 'icon_source_url',
            'color_variant', 'is_verified'
        ]
        read_only_fields = ['id', 'is_verified', 'icon_path']
    
    def get_icon_url(self, obj):
        from .utils import get_absolute_media_url
        return get_absolute_media_url(obj.icon_path)

from .models import (
    Portfolio, PortfolioProfile, PortfolioTech, PortfolioExperience, 
    PortfolioProject, PortfolioEducation, PortfolioSocial
)

# --- Sub-Serializers ---

class PortfolioProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='portfolio.user.name', read_only=True)
    
    class Meta:
        model = PortfolioProfile
        fields = ['headline', 'short_bio', 'long_bio', 'full_name']

class PortfolioTechSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='tech.display_name')
    code = serializers.CharField(source='tech.code_name')
    icon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioTech
        fields = ['name', 'code', 'proficiency', 'icon_url']
        
    def get_icon_url(self, obj):
        if obj.tech.icon_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.tech.icon_path.url)
        return obj.tech.icon_source_url

class PortfolioExperienceSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(format="%Y-%m-%d", allow_null=True)
    end_date = serializers.DateField(format="%Y-%m-%d", allow_null=True)
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioExperience
        fields = ['company_name', 'role', 'start_date', 'end_date', 'is_current', 'description', 'logo_url']
        
    def get_logo_url(self, obj):
        from .utils import get_absolute_media_url
        
        # 1. Direct upload on Experience object
        if obj.logo:
            return get_absolute_media_url(obj.logo)
            
        # 2. Fallback to CompanyRegistry
        if obj.company:
            # Registry has file?
            if obj.company.logo_file:
                return get_absolute_media_url(obj.company.logo_file)
            # Registry has external URL?
            if obj.company.logo_url:
                return obj.company.logo_url
                
        return None

class PortfolioProjectSerializer(serializers.ModelSerializer):
    technologies = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioProject
        fields = [
            'title', 'description', 'repo_url', 'live_url', 'technologies',
            'key_features', 'technical_challenges', 'year', 'project_type', 'thumbnail_url'
        ]
        
    def get_technologies(self, obj):
        # Merge registered techs and missing techs
        registered = [t.code_name for t in obj.tech_used.all()]
        missing = obj.missing_technologies or []
        return registered + missing
    
    def get_thumbnail_url(self, obj):
        from .utils import get_absolute_media_url
        return get_absolute_media_url(obj.thumbnail)

class PortfolioEducationSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(format="%Y-%m-%d", allow_null=True)
    end_date = serializers.DateField(format="%Y-%m-%d", allow_null=True)
    
    class Meta:
        model = PortfolioEducation
        fields = ['institution', 'degree', 'start_date', 'end_date', 'description']

class PortfolioSocialSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source='social_platform.code_name')
    
    class Meta:
        model = PortfolioSocial
        fields = ['platform', 'url']

# --- Main Composition Serializer ---

class PortfolioCompositionSerializer(serializers.ModelSerializer):
    hero = serializers.SerializerMethodField()
    about = serializers.SerializerMethodField()
    socials = serializers.SerializerMethodField()
    tech_stack = serializers.SerializerMethodField()
    experience = PortfolioExperienceSerializer(source='experiences', many=True)
    projects = PortfolioProjectSerializer(many=True)
    education = PortfolioEducationSerializer(many=True) # Assuming frontend might use it
    
    class Meta:
        model = Portfolio
        fields = ['hero', 'about', 'socials', 'tech_stack', 'experience', 'projects', 'education']
        
    def get_hero(self, obj):
        # Construct Hero object
        # Needs: full_name, headline, short_bio, profile_image
        profile = getattr(obj, 'profile', None)
        
        # Profile Image: Try Resume.profile_photo first (legacy/easy access)
        # Or look for Media objects
        resume = Resume.objects.filter(user=obj.user).first()
        photo_url = ""
        if resume and resume.profile_photo:
            from .utils import get_absolute_media_url
            photo_url = get_absolute_media_url(resume.profile_photo) or ""
        
        return {
            "full_name": obj.user.name,
            "headline": profile.headline if profile else "",
            "short_bio": profile.short_bio if profile else "",
            "profile_image": photo_url
        }
        
    def get_about(self, obj):
        profile = getattr(obj, 'profile', None)
        return {
            "long_bio": profile.long_bio if profile else ""
        }
        
    def get_socials(self, obj):
        # Flatten list to dict: {"github": "url", ...}
        socials_qs = obj.socials.all()
        result = {}
        for s in socials_qs:
            result[s.social_platform.code_name] = s.url
        return result
        
    def get_tech_stack(self, obj):
        # List of strings (code_names) from registered tech
        registered = [t.tech.code_name for t in obj.tech_stack.all().select_related('tech')]
        # Add missing tech
        missing = obj.missing_tech_stack if obj.missing_tech_stack else []
        return registered + missing

from rest_framework import serializers
from .models import CompanyRegistry

class CompanyRegistrySerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyRegistry
        fields = ['id', 'name', 'domain', 'logo_url', 'is_verified']
    
    def get_logo_url(self, obj):
        from .utils import get_absolute_media_url
        
        # Priority: logo_file > logo_url
        if obj.logo_file:
            return get_absolute_media_url(obj.logo_file)
        
        if obj.logo_url:
            return obj.logo_url
            
        return None