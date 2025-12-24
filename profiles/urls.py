from .views import (
    ResumeView, ResumeStatusView, ResumeExtractedTextView, 
    PortfolioStructuredDataView, PortfolioPublishStatusView, ConfirmPortfolioView,
    TechSearchAPIView, TechCreateAPIView, TechListAPIView,
    SocialSearchAPIView, SocialCreateAPIView, SocialListAPIView,
    ProfilePhotoUploadView, CompanyLogoUploadView
)
from .views_project import ProjectThumbnailUploadView
from .views_publish import (
    UsernameCheckView,
    UsernameInfoView,
    UsernameChangeView,
    PublishStatusView,
    PublishPortfolioView,
    UnpublishPortfolioView,
    PublishHistoryView,
)
from django.urls import path

urlpatterns = [
    # Resume endpoints
    path('resume/', ResumeView.as_view(), name='resume'),
    path('resume/status/', ResumeStatusView.as_view(), name='resume-status'),
    path('resume/extracted-text/', ResumeExtractedTextView.as_view(), name='resume-extracted-text'),
    
    # Portfolio data endpoints
    path('portfolio/structured/', PortfolioStructuredDataView.as_view(), name='portfolio-structured'),
    path('portfolio/confirm/', ConfirmPortfolioView.as_view(), name='portfolio-confirm'),
    path('portfolio/publish-status/', PortfolioPublishStatusView.as_view(), name='portfolio-publish-status'),
    
    # Username endpoints
    path('username/check/', UsernameCheckView.as_view(), name='username-check'),
    path('username/info/', UsernameInfoView.as_view(), name='username-info'),
    path('username/change/', UsernameChangeView.as_view(), name='username-change'),
    
    # Publishing endpoints
    path('portfolio/publish/', PublishPortfolioView.as_view(), name='portfolio-publish'),
    path('portfolio/publish/status/', PublishStatusView.as_view(), name='publish-status'),
    path('portfolio/publish/history/', PublishHistoryView.as_view(), name='publish-history'),
    path('portfolio/unpublish/', UnpublishPortfolioView.as_view(), name='portfolio-unpublish'),
    
    # Tech and Social registries
    path('tech/search/', TechSearchAPIView.as_view(), name='tech-search'),
    path('tech/list/', TechListAPIView.as_view(), name='tech-list'),
    path('tech/', TechCreateAPIView.as_view(), name='tech-create'),
    path('social/search/', SocialSearchAPIView.as_view(), name='social-search'),
    path('social/list/', SocialListAPIView.as_view(), name='social-list'),
    path('social/', SocialCreateAPIView.as_view(), name='social-create'),
    
    # Media uploads
    path('portfolio/photo/', ProfilePhotoUploadView.as_view(), name='profile-photo-upload'),
    path('portfolio/company-logo/', CompanyLogoUploadView.as_view(), name='company-logo-upload'),
    path('portfolio/project-thumbnail/', ProjectThumbnailUploadView.as_view(), name='project-thumbnail-upload'),
]
