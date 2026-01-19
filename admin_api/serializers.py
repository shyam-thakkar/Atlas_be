"""
Admin API Serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from payments.models import Payment
from profiles.models import (
    Portfolio, PortfolioProfile, PortfolioTech, PortfolioExperience,
    PortfolioProject, PortfolioEducation, PortfolioSocial, PortfolioAISnapshot,
    PublishedSnapshot, Username, ReservedUsername,
    TechRegistry, SocialRegistry, CompanyRegistry,
    Resume, ResumeProcessingStatus
)
from chat.models import RAGDocument, ChatSession, ChatMessage

User = get_user_model()


# ============ USER SERIALIZERS ============

class AdminUserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user list view"""
    portfolio_username = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'user_tier', 'plan_type', 
            'subscription_expiry', 'authentication_method',
            'resume_process_count', 'username_change_count',
            'is_active', 'is_staff', 'created_at', 'last_login',
            'portfolio_username'
        ]
    
    def get_portfolio_username(self, obj):
        try:
            return obj.portfolio_username.username
        except:
            return None


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """Full user details with related data counts"""
    portfolio_username = serializers.SerializerMethodField()
    portfolios_count = serializers.SerializerMethodField()
    payments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'google_id', 'user_tier', 'plan_type',
            'subscription_expiry', 'authentication_method',
            'resume_process_count', 'username_change_count',
            'is_active', 'is_staff', 'is_superuser',
            'created_at', 'last_login',
            'portfolio_username', 'portfolios_count', 'payments_count'
        ]
        read_only_fields = ['email', 'google_id', 'authentication_method', 'created_at', 'last_login']
    
    def get_portfolio_username(self, obj):
        try:
            return obj.portfolio_username.username
        except:
            return None
    
    def get_portfolios_count(self, obj):
        return obj.portfolios.count()
    
    def get_payments_count(self, obj):
        return obj.payments.count()


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user fields"""
    class Meta:
        model = User
        fields = [
            'name', 'user_tier', 'plan_type', 'subscription_expiry',
            'resume_process_count', 'username_change_count',
            'is_active', 'is_staff'
        ]


# ============ PAYMENT SERIALIZERS ============

class AdminPaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'razorpay_order_id', 
            'razorpay_payment_id', 'razorpay_signature',
            'plan_type', 'amount', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'razorpay_order_id', 'razorpay_payment_id',
            'razorpay_signature', 'plan_type', 'amount', 'created_at', 'updated_at'
        ]


# ============ PORTFOLIO SERIALIZERS ============

class AdminPortfolioProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioProfile
        fields = ['id', 'headline', 'short_bio', 'long_bio']


class AdminPortfolioTechSerializer(serializers.ModelSerializer):
    tech_name = serializers.CharField(source='tech.display_name', read_only=True)
    
    class Meta:
        model = PortfolioTech
        fields = ['id', 'tech', 'tech_name', 'proficiency', 'display_order']


class AdminPortfolioExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioExperience
        fields = [
            'id', 'company', 'company_name', 'role', 
            'start_date', 'end_date', 'description', 'is_current', 'logo'
        ]


class AdminPortfolioProjectSerializer(serializers.ModelSerializer):
    tech_used_names = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioProject
        fields = [
            'id', 'title', 'description', 'repo_url', 'live_url',
            'tech_used', 'tech_used_names', 'display_order',
            'key_features', 'technical_challenges', 'year',
            'project_type', 'thumbnail', 'missing_technologies'
        ]
    
    def get_tech_used_names(self, obj):
        return [t.display_name for t in obj.tech_used.all()]


class AdminPortfolioEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioEducation
        fields = [
            'id', 'institution', 'degree', 'field_of_study',
            'grade', 'grade_type', 'start_date', 'end_date', 'description'
        ]


class AdminPortfolioSocialSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source='social_platform.display_name', read_only=True)
    
    class Meta:
        model = PortfolioSocial
        fields = ['id', 'social_platform', 'platform_name', 'url']


class AdminPublishedSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishedSnapshot
        fields = ['id', 'version', 'snapshot_data', 'is_active', 'published_at']
        read_only_fields = ['version', 'published_at']


class AdminPortfolioListSerializer(serializers.ModelSerializer):
    """Lightweight for list view"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='username.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'user', 'user_email', 'title', 'theme', 'username',
            'is_published', 'created_at', 'updated_at'
        ]


class AdminPortfolioDetailSerializer(serializers.ModelSerializer):
    """Full portfolio with all nested data"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    username_str = serializers.CharField(source='username.username', read_only=True, allow_null=True)
    profile = AdminPortfolioProfileSerializer(read_only=True)
    tech_stack = AdminPortfolioTechSerializer(many=True, read_only=True)
    experiences = AdminPortfolioExperienceSerializer(many=True, read_only=True)
    projects = AdminPortfolioProjectSerializer(many=True, read_only=True)
    education = AdminPortfolioEducationSerializer(many=True, read_only=True)
    socials = AdminPortfolioSocialSerializer(many=True, read_only=True)
    published_snapshots = AdminPublishedSnapshotSerializer(many=True, read_only=True)
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'user', 'user_email', 'title', 'theme', 'username', 'username_str',
            'missing_tech_stack', 'contact_data', 'is_published', 'public_url',
            'created_at', 'updated_at',
            'profile', 'tech_stack', 'experiences', 'projects', 
            'education', 'socials', 'published_snapshots'
        ]
        read_only_fields = ['user', 'is_published', 'public_url', 'created_at', 'updated_at']


# ============ REGISTRY SERIALIZERS ============

class AdminTechRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TechRegistry
        fields = [
            'id', 'display_name', 'code_name', 'icon_type', 'icon_path',
            'icon_source_url', 'doc_url', 'color_variant',
            'created_by_user', 'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AdminSocialRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialRegistry
        fields = [
            'id', 'display_name', 'code_name', 'icon_type', 'icon_path',
            'icon_source_url', 'color_variant',
            'created_by_user', 'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AdminCompanyRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyRegistry
        fields = [
            'id', 'name', 'domain', 'logo_file', 'logo_url',
            'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AdminUsernameSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Username
        fields = ['id', 'username', 'user', 'user_email', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class AdminReservedUsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservedUsername
        fields = ['id', 'username', 'reason', 'created_at']
        read_only_fields = ['created_at']


# ============ CHAT SERIALIZERS ============

class AdminChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'retrieved_documents', 'timestamp']
        read_only_fields = ['timestamp']


class AdminChatSessionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    messages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'session_id', 'user', 'user_email', 'portfolio',
            'is_public', 'is_active', 'created_at', 'last_activity',
            'user_agent', 'ip_address', 'messages_count'
        ]
        read_only_fields = ['session_id', 'created_at', 'last_activity']
    
    def get_messages_count(self, obj):
        return obj.messages.count()


class AdminChatSessionDetailSerializer(AdminChatSessionSerializer):
    messages = AdminChatMessageSerializer(many=True, read_only=True)
    
    class Meta(AdminChatSessionSerializer.Meta):
        fields = AdminChatSessionSerializer.Meta.fields + ['messages']


class AdminRAGDocumentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = RAGDocument
        fields = [
            'id', 'user', 'user_email', 'portfolio_version',
            'title', 'text', 'section', 'source',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'portfolio_version', 'created_at', 'updated_at']


# ============ RESUME SERIALIZERS ============

class AdminResumeProcessingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeProcessingStatus
        fields = ['id', 'status', 'error_message', 'updated_at']
        read_only_fields = ['updated_at']


class AdminResumeSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    processing_status = AdminResumeProcessingStatusSerializer(read_only=True)
    
    class Meta:
        model = Resume
        fields = [
            'id', 'user', 'user_email', 'original_filename', 'file',
            'profile_photo', 'extracted_text', 'structured_data',
            'uploaded_at', 'processing_status'
        ]
        read_only_fields = ['user', 'uploaded_at']
