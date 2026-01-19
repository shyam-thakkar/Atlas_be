"""
Admin API URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import (
    # Auth
    AdminLoginView, AdminMeView, AdminLogoutView,
    # Dashboard
    DashboardStatsView,
    AdminUserViewSet,
    AdminPaymentViewSet,
    AdminPortfolioViewSet,
    AdminPortfolioExperienceViewSet,
    AdminPortfolioProjectViewSet,
    AdminPortfolioEducationViewSet,
    AdminPortfolioTechViewSet,
    AdminPortfolioSocialViewSet,
    AdminTechRegistryViewSet,
    AdminSocialRegistryViewSet,
    AdminCompanyRegistryViewSet,
    AdminUsernameViewSet,
    AdminReservedUsernameViewSet,
    AdminChatSessionViewSet,
    AdminRAGDocumentViewSet,
    AdminResumeViewSet,
)

# Main router
router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='admin-users')
router.register(r'payments', AdminPaymentViewSet, basename='admin-payments')
router.register(r'portfolios', AdminPortfolioViewSet, basename='admin-portfolios')
router.register(r'tech-registry', AdminTechRegistryViewSet, basename='admin-tech-registry')
router.register(r'social-registry', AdminSocialRegistryViewSet, basename='admin-social-registry')
router.register(r'company-registry', AdminCompanyRegistryViewSet, basename='admin-company-registry')
router.register(r'usernames', AdminUsernameViewSet, basename='admin-usernames')
router.register(r'reserved-usernames', AdminReservedUsernameViewSet, basename='admin-reserved-usernames')
router.register(r'chat-sessions', AdminChatSessionViewSet, basename='admin-chat-sessions')
router.register(r'rag-documents', AdminRAGDocumentViewSet, basename='admin-rag-documents')
router.register(r'resumes', AdminResumeViewSet, basename='admin-resumes')

# Nested routers for portfolio sub-resources
portfolios_router = nested_routers.NestedDefaultRouter(router, r'portfolios', lookup='portfolio')
portfolios_router.register(r'experiences', AdminPortfolioExperienceViewSet, basename='admin-portfolio-experiences')
portfolios_router.register(r'projects', AdminPortfolioProjectViewSet, basename='admin-portfolio-projects')
portfolios_router.register(r'education', AdminPortfolioEducationViewSet, basename='admin-portfolio-education')
portfolios_router.register(r'tech-stack', AdminPortfolioTechViewSet, basename='admin-portfolio-tech')
portfolios_router.register(r'socials', AdminPortfolioSocialViewSet, basename='admin-portfolio-socials')

urlpatterns = [
    # Auth endpoints
    path('auth/login/', AdminLoginView.as_view(), name='admin-login'),
    path('auth/me/', AdminMeView.as_view(), name='admin-me'),
    path('auth/logout/', AdminLogoutView.as_view(), name='admin-logout'),
    # Dashboard
    path('dashboard/stats/', DashboardStatsView.as_view(), name='admin-dashboard-stats'),
    # CRUD endpoints
    path('', include(router.urls)),
    path('', include(portfolios_router.urls)),
]
