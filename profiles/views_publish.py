"""
Views for portfolio publishing workflow.
Handles username checking, claiming, changing, publishing, and public access.
"""
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction

from .models import Portfolio, Username
from .username_utils import (
    validate_username_format,
    is_username_available,
    is_username_reserved,
    claim_username,
    change_username,
    get_username_info,
    UsernameValidationError,
    UsernameReservedError,
    UsernameTakenError,
    UsernameChangeLimitError,
    UsernameError,
)
from .snapshot_service import (
    publish_portfolio,
    unpublish_portfolio,
    get_public_snapshot,
    get_snapshot_history,
)


class UsernameCheckView(APIView):
    """
    Check if a username is available.
    GET /api/profile/username/check/?username=johndoe
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        username = request.GET.get('username', '')
        
        if not username:
            return Response(
                {'error': 'Username parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            normalized = validate_username_format(username)
        except UsernameValidationError as e:
            return Response({
                'available': False,
                'username': username,
                'reason': str(e)
            })
        
        if is_username_reserved(normalized):
            return Response({
                'available': False,
                'username': normalized,
                'reason': 'This username is reserved'
            })
        
        # Exclude current user if authenticated
        exclude_user = request.user if request.user.is_authenticated else None
        available = is_username_available(normalized, exclude_user=exclude_user)
        
        return Response({
            'available': available,
            'username': normalized,
            'reason': None if available else 'Username is already taken'
        })


class UsernameInfoView(APIView):
    """
    Get current user's username info and change limits.
    GET /api/profile/username/info/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        info = get_username_info(request.user)
        return Response(info)


class UsernameChangeView(APIView):
    """
    Change the user's username (subject to tier limits).
    POST /api/profile/username/change/
    Body: {"username": "newusername"}
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        new_username = request.data.get('username')
        
        if not new_username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            username_obj = change_username(request.user, new_username)
            
            # Get updated portfolio info
            portfolio = Portfolio.objects.filter(user=request.user).first()
            
            return Response({
                'success': True,
                'message': 'Username changed successfully!',
                'username': username_obj.username,
                'public_url': portfolio.public_url if portfolio else None,
                'changes_remaining': request.user.get_remaining_username_changes(),
            })
            
        except UsernameChangeLimitError as e:
            return Response({
                'error': str(e),
                'changes_remaining': 0,
                'upgrade_required': True,
            }, status=status.HTTP_403_FORBIDDEN)
        except UsernameValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except UsernameReservedError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except UsernameTakenError as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
        except UsernameError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PublishStatusView(APIView):
    """
    Get current publish status of user's portfolio.
    GET /api/profile/portfolio/publish/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            portfolio = Portfolio.objects.get(user=request.user)
        except Portfolio.DoesNotExist:
            return Response({
                'has_portfolio': False,
                'is_published': False,
                'username': None,
                'public_url': None,
            })
        
        # Get username info
        username_info = get_username_info(request.user)
        
        # Get active snapshot
        active_snapshot = portfolio.active_snapshot
        
        return Response({
            'has_portfolio': True,
            'is_published': active_snapshot is not None,
            'username': username_info['username'],
            'public_url': portfolio.public_url,
            'current_version': active_snapshot.version if active_snapshot else None,
            'published_at': active_snapshot.published_at if active_snapshot else None,
            'total_versions': portfolio.published_snapshots.count(),
            'can_change_username': username_info['can_change'],
            'username_changes_remaining': username_info['changes_remaining'],
        })


class PublishPortfolioView(APIView):
    """
    Publish or republish a portfolio.
    
    First publish: requires username selection
    Republish: creates new snapshot
    
    POST /api/profile/portfolio/publish/
    Body (first publish): {"username": "johndoe"}
    Body (republish): {} or no body needed
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            portfolio = Portfolio.objects.select_related('username').get(user=request.user)
        except Portfolio.DoesNotExist:
            return Response(
                {'error': 'No portfolio found. Please create a portfolio first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if this is first publish (no username yet)
        has_username = hasattr(request.user, 'portfolio_username') and request.user.portfolio_username is not None
        
        if not has_username:
            # FIRST PUBLISH: Require username
            username = request.data.get('username')
            if not username:
                return Response(
                    {
                        'error': 'Username is required for first publish',
                        'first_publish': True,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                with transaction.atomic():
                    # Claim username (this also links it to portfolio)
                    username_obj = claim_username(request.user, username)
                    
                    # Refresh portfolio to get the updated username
                    portfolio.refresh_from_db()
                    
                    # Create snapshot
                    snapshot = publish_portfolio(portfolio)
                
                return Response({
                    'success': True,
                    'message': 'Portfolio published successfully!',
                    'first_publish': True,
                    'username': username_obj.username,
                    'public_url': portfolio.public_url,
                    'version': snapshot.version,
                })
                
            except UsernameValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except UsernameReservedError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except UsernameTakenError as e:
                return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
            except UsernameError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            # REPUBLISH: Create new snapshot
            try:
                snapshot = publish_portfolio(portfolio)
                
                return Response({
                    'success': True,
                    'message': 'Portfolio republished successfully!',
                    'first_publish': False,
                    'username': request.user.portfolio_username.username,
                    'public_url': portfolio.public_url,
                    'version': snapshot.version,
                })
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UnpublishPortfolioView(APIView):
    """
    Unpublish a portfolio (makes it private).
    Username is retained.
    
    POST /api/profile/portfolio/unpublish/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            portfolio = Portfolio.objects.get(user=request.user)
        except Portfolio.DoesNotExist:
            return Response(
                {'error': 'No portfolio found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        was_published = unpublish_portfolio(portfolio)
        
        username = None
        if hasattr(request.user, 'portfolio_username') and request.user.portfolio_username:
            username = request.user.portfolio_username.username
        
        if was_published:
            return Response({
                'success': True,
                'message': 'Portfolio unpublished. Your username is still reserved.',
                'username': username,
            })
        else:
            return Response({
                'success': True,
                'message': 'Portfolio was already unpublished.',
                'username': username,
            })


class PublishHistoryView(APIView):
    """
    Get publish version history for user's portfolio.
    GET /api/profile/portfolio/publish/history/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            portfolio = Portfolio.objects.get(user=request.user)
        except Portfolio.DoesNotExist:
            return Response(
                {'error': 'No portfolio found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        history = get_snapshot_history(portfolio, include_data=False)
        
        return Response({
            'total_versions': len(history),
            'history': history,
        })


class PublicPortfolioView(APIView):
    """
    Public endpoint to fetch a published portfolio by username.
    No authentication required.
    
    GET /api/public/portfolio/{username}/
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, username):
        snapshot_data = get_public_snapshot(username)
        
        if snapshot_data is None:
            return Response(
                {'error': 'Portfolio not found or not published'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(snapshot_data)
