"""
Admin API Views - Complete CRUD for all entities
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta

from .permissions import IsAdminUser
from .serializers import (
    AdminUserListSerializer, AdminUserDetailSerializer, AdminUserUpdateSerializer,
    AdminPaymentSerializer,
    AdminPortfolioListSerializer, AdminPortfolioDetailSerializer,
    AdminPortfolioProfileSerializer, AdminPortfolioTechSerializer,
    AdminPortfolioExperienceSerializer, AdminPortfolioProjectSerializer,
    AdminPortfolioEducationSerializer, AdminPortfolioSocialSerializer,
    AdminPublishedSnapshotSerializer,
    AdminTechRegistrySerializer, AdminSocialRegistrySerializer,
    AdminCompanyRegistrySerializer, AdminUsernameSerializer, AdminReservedUsernameSerializer,
    AdminChatSessionSerializer, AdminChatSessionDetailSerializer, AdminRAGDocumentSerializer,
    AdminResumeSerializer
)
from payments.models import Payment
from profiles.models import (
    Portfolio, PortfolioProfile, PortfolioTech, PortfolioExperience,
    PortfolioProject, PortfolioEducation, PortfolioSocial,
    PublishedSnapshot, Username, ReservedUsername,
    TechRegistry, SocialRegistry, CompanyRegistry,
    Resume
)
from chat.models import RAGDocument, ChatSession

User = get_user_model()


class AdminPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============ AUTHENTICATION ============

class AdminLoginView(APIView):
    """
    Admin Login - Authenticate and verify admin status
    Returns JWT tokens only if user is staff/superuser
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is active
        if not user.is_active:
            return Response(
                {'error': 'Account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user is admin (staff or superuser)
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'Access denied. Admin privileges required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })


class AdminMeView(APIView):
    """
    Get current admin user info - Verify if authenticated user is admin
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        is_admin = user.is_staff or user.is_superuser
        
        return Response({
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_admin': is_admin,
            'is_active': user.is_active,
        })


class AdminLogoutView(APIView):
    """
    Admin Logout - Blacklist the refresh token
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logout successful'})
        except Exception:
            return Response({'message': 'Logout successful'})


# ============ DASHBOARD ============

class DashboardStatsView(APIView):
    """Dashboard statistics overview"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        stats = {
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True).count(),
                'by_tier': {
                    'free': User.objects.filter(user_tier='free').count(),
                    'pro': User.objects.filter(user_tier='pro').count(),
                    'lifetime': User.objects.filter(user_tier='lifetime').count(),
                },
                'new_this_month': User.objects.filter(created_at__gte=month_start).count(),
            },
            'revenue': {
                'total': Payment.objects.filter(status='success').aggregate(
                    total=Sum('amount'))['total'] or 0,
                'this_month': Payment.objects.filter(
                    status='success', created_at__gte=month_start
                ).aggregate(total=Sum('amount'))['total'] or 0,
                'pending_payments': Payment.objects.filter(status='pending').count(),
            },
            'portfolios': {
                'total': Portfolio.objects.count(),
                'published': Portfolio.objects.filter(
                    published_snapshots__is_active=True
                ).distinct().count(),
            },
            'chat': {
                'total_sessions': ChatSession.objects.count(),
                'active_sessions': ChatSession.objects.filter(is_active=True).count(),
                'total_rag_documents': RAGDocument.objects.count(),
            },
            'resumes': {
                'total': Resume.objects.count(),
            }
        }
        return Response(stats)


# ============ USER MANAGEMENT ============

class AdminUserViewSet(viewsets.ModelViewSet):
    """Full user management"""
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = User.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AdminUserListSerializer
        elif self.action in ['update', 'partial_update']:
            return AdminUserUpdateSerializer
        return AdminUserDetailSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filter by tier
        tier = self.request.query_params.get('tier')
        if tier:
            qs = qs.filter(user_tier=tier)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        
        # Search by email or name
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(email__icontains=search) | Q(name__icontains=search))
        
        return qs
    
    @action(detail=True, methods=['post'])
    def upgrade(self, request, pk=None):
        """Upgrade user tier manually"""
        user = self.get_object()
        new_tier = request.data.get('tier')
        new_plan = request.data.get('plan_type')
        
        if new_tier not in ['free', 'pro', 'lifetime']:
            return Response({'error': 'Invalid tier'}, status=400)
        
        user.user_tier = new_tier
        if new_plan:
            user.plan_type = new_plan
        
        # Set subscription expiry for pro tier
        if new_tier == 'pro':
            days = request.data.get('days', 30)
            if user.subscription_expiry and user.subscription_expiry > timezone.now():
                user.subscription_expiry += timedelta(days=days)
            else:
                user.subscription_expiry = timezone.now() + timedelta(days=days)
        elif new_tier == 'lifetime':
            user.subscription_expiry = None  # No expiry for lifetime
        
        user.save()
        return Response(AdminUserDetailSerializer(user).data)
    
    @action(detail=True, methods=['post'])
    def extend_subscription(self, request, pk=None):
        """Extend subscription by X days"""
        user = self.get_object()
        days = request.data.get('days', 30)
        
        if user.subscription_expiry and user.subscription_expiry > timezone.now():
            user.subscription_expiry += timedelta(days=days)
        else:
            user.subscription_expiry = timezone.now() + timedelta(days=days)
        
        user.save()
        return Response({'message': f'Extended by {days} days', 'new_expiry': user.subscription_expiry})
    
    @action(detail=True, methods=['post'])
    def reset_counts(self, request, pk=None):
        """Reset resume/username change counts"""
        user = self.get_object()
        reset_type = request.data.get('type', 'all')
        
        if reset_type in ['resume', 'all']:
            user.resume_process_count = 0
        if reset_type in ['username', 'all']:
            user.username_change_count = 0
        
        user.save()
        return Response({'message': 'Counts reset successfully'})


# ============ PAYMENT MANAGEMENT ============

class AdminPaymentViewSet(viewsets.ModelViewSet):
    """Payment management - mostly read-only"""
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = Payment.objects.all().select_related('user').order_by('-created_at')
    serializer_class = AdminPaymentSerializer
    http_method_names = ['get', 'patch', 'head', 'options']  # No create/delete
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        # Filter by plan
        plan = self.request.query_params.get('plan_type')
        if plan:
            qs = qs.filter(plan_type=plan)
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)
        
        return qs


# ============ PORTFOLIO MANAGEMENT ============

class AdminPortfolioViewSet(viewsets.ModelViewSet):
    """Portfolio management with all sub-resources"""
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = Portfolio.objects.all().select_related(
        'user', 'username', 'profile'
    ).prefetch_related(
        'tech_stack', 'experiences', 'projects', 
        'education', 'socials', 'published_snapshots'
    ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AdminPortfolioListSerializer
        return AdminPortfolioDetailSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)
        
        # Filter by published status
        published = self.request.query_params.get('published')
        if published is not None:
            if published.lower() == 'true':
                qs = qs.filter(published_snapshots__is_active=True).distinct()
            else:
                qs = qs.exclude(published_snapshots__is_active=True)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(user__email__icontains=search) | 
                Q(title__icontains=search) |
                Q(username__username__icontains=search)
            )
        
        return qs
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish portfolio by deactivating all snapshots"""
        portfolio = self.get_object()
        count = portfolio.published_snapshots.filter(is_active=True).update(is_active=False)
        return Response({'message': f'Unpublished {count} snapshot(s)'})
    
    # ---- Snapshot Management ----
    @action(detail=True, methods=['get'])
    def snapshots(self, request, pk=None):
        """Get all snapshots (active and archived)"""
        portfolio = self.get_object()
        snapshots = portfolio.published_snapshots.all().order_by('-version')
        serializer = AdminPublishedSnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='snapshots/(?P<snapshot_id>[^/.]+)/activate')
    def activate_snapshot(self, request, pk=None, snapshot_id=None):
        """Activate a specific snapshot (rollback)"""
        portfolio = self.get_object()
        
        # Deactivate all current snapshots
        portfolio.published_snapshots.update(is_active=False)
        
        # Activate the specified one
        try:
            snapshot = portfolio.published_snapshots.get(id=snapshot_id)
            snapshot.is_active = True
            snapshot.save()
            return Response({'message': f'Activated snapshot v{snapshot.version}'})
        except PublishedSnapshot.DoesNotExist:
            return Response({'error': 'Snapshot not found'}, status=404)
    
    @action(detail=True, methods=['delete'], url_path='snapshots/(?P<snapshot_id>[^/.]+)')
    def delete_snapshot(self, request, pk=None, snapshot_id=None):
        """Delete an archived snapshot"""
        portfolio = self.get_object()
        try:
            snapshot = portfolio.published_snapshots.get(id=snapshot_id)
            if snapshot.is_active:
                return Response({'error': 'Cannot delete active snapshot'}, status=400)
            snapshot.delete()
            return Response({'message': 'Snapshot deleted'})
        except PublishedSnapshot.DoesNotExist:
            return Response({'error': 'Snapshot not found'}, status=404)


# ============ PORTFOLIO SUB-RESOURCES ============

class AdminPortfolioExperienceViewSet(viewsets.ModelViewSet):
    """Experience CRUD for a portfolio"""
    permission_classes = [IsAdminUser]
    serializer_class = AdminPortfolioExperienceSerializer
    
    def get_queryset(self):
        return PortfolioExperience.objects.filter(
            portfolio_id=self.kwargs['portfolio_pk']
        )
    
    def perform_create(self, serializer):
        serializer.save(portfolio_id=self.kwargs['portfolio_pk'])


class AdminPortfolioProjectViewSet(viewsets.ModelViewSet):
    """Project CRUD for a portfolio"""
    permission_classes = [IsAdminUser]
    serializer_class = AdminPortfolioProjectSerializer
    
    def get_queryset(self):
        return PortfolioProject.objects.filter(
            portfolio_id=self.kwargs['portfolio_pk']
        )
    
    def perform_create(self, serializer):
        serializer.save(portfolio_id=self.kwargs['portfolio_pk'])


class AdminPortfolioEducationViewSet(viewsets.ModelViewSet):
    """Education CRUD for a portfolio"""
    permission_classes = [IsAdminUser]
    serializer_class = AdminPortfolioEducationSerializer
    
    def get_queryset(self):
        return PortfolioEducation.objects.filter(
            portfolio_id=self.kwargs['portfolio_pk']
        )
    
    def perform_create(self, serializer):
        serializer.save(portfolio_id=self.kwargs['portfolio_pk'])


class AdminPortfolioTechViewSet(viewsets.ModelViewSet):
    """Tech stack CRUD for a portfolio"""
    permission_classes = [IsAdminUser]
    serializer_class = AdminPortfolioTechSerializer
    
    def get_queryset(self):
        return PortfolioTech.objects.filter(
            portfolio_id=self.kwargs['portfolio_pk']
        )
    
    def perform_create(self, serializer):
        serializer.save(portfolio_id=self.kwargs['portfolio_pk'])


class AdminPortfolioSocialViewSet(viewsets.ModelViewSet):
    """Socials CRUD for a portfolio"""
    permission_classes = [IsAdminUser]
    serializer_class = AdminPortfolioSocialSerializer
    
    def get_queryset(self):
        return PortfolioSocial.objects.filter(
            portfolio_id=self.kwargs['portfolio_pk']
        )
    
    def perform_create(self, serializer):
        serializer.save(portfolio_id=self.kwargs['portfolio_pk'])


# ============ REGISTRY MANAGEMENT ============

class AdminTechRegistryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = TechRegistry.objects.all().order_by('display_name')
    serializer_class = AdminTechRegistrySerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(display_name__icontains=search) | Q(code_name__icontains=search)
            )
        verified = self.request.query_params.get('verified')
        if verified is not None:
            qs = qs.filter(is_verified=verified.lower() == 'true')
        return qs


class AdminSocialRegistryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = SocialRegistry.objects.all().order_by('display_name')
    serializer_class = AdminSocialRegistrySerializer


class AdminCompanyRegistryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = CompanyRegistry.objects.all().order_by('name')
    serializer_class = AdminCompanyRegistrySerializer


class AdminUsernameViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = Username.objects.all().select_related('user').order_by('username')
    serializer_class = AdminUsernameSerializer


class AdminReservedUsernameViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = ReservedUsername.objects.all().order_by('username')
    serializer_class = AdminReservedUsernameSerializer


# ============ CHAT MANAGEMENT ============

class AdminChatSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = ChatSession.objects.all().select_related('user', 'portfolio').order_by('-last_activity')
    http_method_names = ['get', 'patch', 'head', 'options']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminChatSessionDetailSerializer
        return AdminChatSessionSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return qs
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """Terminate an active session"""
        session = self.get_object()
        session.is_active = False
        session.save()
        return Response({'message': 'Session terminated'})


class AdminRAGDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = RAGDocument.objects.all().select_related('user').order_by('-created_at')
    serializer_class = AdminRAGDocumentSerializer
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']
    
    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)
        section = self.request.query_params.get('section')
        if section:
            qs = qs.filter(section=section)
        return qs


# ============ RESUME MANAGEMENT ============

class AdminResumeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = AdminPagination
    queryset = Resume.objects.all().select_related('user', 'processing_status').order_by('-uploaded_at')
    serializer_class = AdminResumeSerializer
    http_method_names = ['get', 'patch', 'head', 'options']
    
    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs
