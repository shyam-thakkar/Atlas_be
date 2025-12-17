from .views import ResumeView, ResumeStatusView, ResumeExtractedTextView, PortfolioStructuredDataView
from django.urls import path
urlpatterns = [
    path('resume/', ResumeView.as_view(), name='resume'),
    path('resume/status/', ResumeStatusView.as_view(), name='resume-status'),
    path('resume/extracted-text/', ResumeExtractedTextView.as_view(), name='resume-extracted-text'),
    path('portfolio/structured/', PortfolioStructuredDataView.as_view(), name='portfolio-structured'),
]
