"""
REST API Views for Chat
Handles session creation and history retrieval
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from profiles.models import Username, Portfolio
from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer

logger = logging.getLogger(__name__)


class CreateSessionView(APIView):
    """
    Create a new chat session for authenticated dashboard users.
    
    POST /api/chat/session/
    
    Returns:
        session_id: UUID for WebSocket connection
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Get user's portfolio
        portfolio = user.portfolios.first()
        
        if not portfolio:
            return Response(
                {"error": "No portfolio found. Please create a portfolio first."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create new session
        session = ChatSession.objects.create(
            user=user,
            portfolio=portfolio,
            is_public=False,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            "session_id": str(session.session_id),
            "is_public": False,
            "created_at": session.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class CreatePublicSessionView(APIView):
    """
    Create or retrieve a public chat session for a published portfolio.
    
    POST /api/chat/session/public/<username>/
    
    This endpoint:
    - Resolves username to portfolio owner
    - Validates portfolio is published
    - Creates or returns existing public session
    
    Returns:
        session_id: UUID for WebSocket connection
    """
    permission_classes = [AllowAny]
    
    def post(self, request, username):
        try:
            # Resolve username to portfolio
            portfolio_username = Username.objects.select_related(
                'user', 'portfolio'
            ).get(username=username.lower())
            
        except Username.DoesNotExist:
            return Response(
                {"error": "Portfolio not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = portfolio_username.user
        portfolio = portfolio_username.portfolio
        
        if not portfolio:
            return Response(
                {"error": "Portfolio not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if portfolio is published
        if not portfolio.is_published:
            return Response(
                {"error": "This portfolio is not published"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get or create public session for this visitor
        # Note: We create per-visitor sessions for isolation
        session = ChatSession.objects.create(
            user=user,  # Portfolio owner
            portfolio=portfolio,
            is_public=True,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            "session_id": str(session.session_id),
            "is_public": True,
            "portfolio_owner": user.name or user.email.split('@')[0],
            "created_at": session.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class ChatHistoryView(APIView):
    """
    Get paginated chat history for a session.
    
    GET /api/chat/history/<session_id>/?page=1&page_size=20
    
    Validates session ownership:
    - For private sessions: user must be authenticated and own the session
    - For public sessions: anyone can access
    """
    permission_classes = [AllowAny]  # Custom validation below
    
    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate access
        if not session.is_public:
            # Private session - must be authenticated owner
            if not request.user.is_authenticated:
                return Response(
                    {"error": "Authentication required"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            if request.user.id != session.user_id:
                return Response(
                    {"error": "Access denied"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Parse pagination
        try:
            page = max(1, int(request.GET.get('page', 1)))
            page_size = min(100, max(1, int(request.GET.get('page_size', 20))))
        except ValueError:
            page = 1
            page_size = 20
        
        # Get messages
        all_messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
        total_messages = all_messages.count()
        
        # Calculate pagination
        total_pages = max(1, (total_messages + page_size - 1) // page_size)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        paginated_messages = all_messages[start_index:end_index]
        
        # Serialize
        serializer = ChatMessageSerializer(paginated_messages, many=True)
        
        return Response({
            "session_id": str(session.session_id),
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "messages": serializer.data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_messages": total_messages,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        })


class DeleteSessionView(APIView):
    """
    Delete a chat session.
    
    DELETE /api/chat/session/<session_id>/
    
    Only the session owner can delete.
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, session_id):
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify ownership
        if request.user.id != session.user_id:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Count messages for response
        message_count = session.messages.count()
        session_id_str = str(session.session_id)
        
        # Delete
        session.delete()
        
        return Response({
            "message": "Session deleted successfully",
            "session_id": session_id_str,
            "deleted_messages": message_count
        })


class RAGStatusView(APIView):
    """
    Get RAG document status for a user.
    
    GET /api/chat/rag/status/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import RAGDocument
        
        docs = RAGDocument.objects.filter(user=request.user)
        
        # Count by section
        section_counts = {}
        for section, _ in RAGDocument.SECTION_CHOICES:
            section_counts[section] = docs.filter(section=section).count()
        
        return Response({
            "total_documents": docs.count(),
            "sections": section_counts,
            "last_updated": docs.order_by('-updated_at').first().updated_at.isoformat() if docs.exists() else None
        })


class TriggerRAGRebuildView(APIView):
    """
    Manually trigger RAG document rebuild.
    
    POST /api/chat/rag/rebuild/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from .tasks import rebuild_user_rag_documents
        
        # Trigger async rebuild
        task = rebuild_user_rag_documents.delay(request.user.id)
        
        return Response({
            "message": "RAG rebuild started",
            "task_id": str(task.id)
        }, status=status.HTTP_202_ACCEPTED)
