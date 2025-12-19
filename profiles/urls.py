from .views import (
    ResumeView, ResumeStatusView, ResumeExtractedTextView, 
    PortfolioStructuredDataView, PortfolioPublishStatusView, ConfirmPortfolioView,
    TechSearchAPIView, TechCreateAPIView, TechListAPIView,
    SocialSearchAPIView, SocialCreateAPIView, SocialListAPIView,
    ProfilePhotoUploadView, CompanyLogoUploadView
)
from .views_project import ProjectThumbnailUploadView
from django.urls import path

urlpatterns = [
    path('resume/', ResumeView.as_view(), name='resume'),
    path('resume/status/', ResumeStatusView.as_view(), name='resume-status'),
    path('resume/extracted-text/', ResumeExtractedTextView.as_view(), name='resume-extracted-text'),
    path('portfolio/structured/', PortfolioStructuredDataView.as_view(), name='portfolio-structured'),
    path('portfolio/confirm/', ConfirmPortfolioView.as_view(), name='portfolio-confirm'),
    path('portfolio/publish-status/', PortfolioPublishStatusView.as_view(), name='portfolio-publish-status'),
    path('tech/search/', TechSearchAPIView.as_view(), name='tech-search'),
    path('tech/list/', TechListAPIView.as_view(), name='tech-list'),
    path('tech/', TechCreateAPIView.as_view(), name='tech-create'),
    path('social/search/', SocialSearchAPIView.as_view(), name='social-search'),
    path('social/list/', SocialListAPIView.as_view(), name='social-list'),
    path('social/', SocialCreateAPIView.as_view(), name='social-create'),
    path('portfolio/photo/', ProfilePhotoUploadView.as_view(), name='profile-photo-upload'),
    path('portfolio/company-logo/', CompanyLogoUploadView.as_view(), name='company-logo-upload'),
    path('portfolio/project-thumbnail/', ProjectThumbnailUploadView.as_view(), name='project-thumbnail-upload'),
]
