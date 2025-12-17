"""
API Views for Chat History
WebSocket handles real-time chat, this provides history retrieval
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import logging

from .models import ChatSession, ChatHistory

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def chat_history(request, session_id):
    """
    Get paginated chat history for a specific session
    
    GET /chat/history/<session_id>/?page=1&page_size=20
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Messages per page (default: 20, max: 100)
    
    Returns:
    {
        "session_id": "uuid",
        "messages": [...],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total_messages": 45,
            "total_pages": 3,
            "has_next": true,
            "has_previous": false
        },
        "success": true
    }
    """
    try:
        # Get session
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({
                "error": "Session not found",
                "success": False
            }, status=404)
        
        # Parse pagination parameters
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
        except ValueError:
            return JsonResponse({
                "error": "Invalid pagination parameters",
                "success": False
            }, status=400)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100
        
        # Get all messages for this session
        all_messages = ChatHistory.objects.filter(session=session).order_by('timestamp')
        total_messages = all_messages.count()
        
        # Calculate pagination
        total_pages = (total_messages + page_size - 1) // page_size if total_messages > 0 else 1
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        # Get paginated messages
        paginated_messages = all_messages[start_index:end_index]
        
        # Format messages
        formatted_messages = []
        for msg in paginated_messages:
            formatted_messages.append({
                "query": msg.user_query,
                "response": msg.bot_response,
                "timestamp": msg.timestamp.isoformat(),
                "retrieved_documents": msg.retrieved_documents
            })
        
        return JsonResponse({
            "session_id": str(session.session_id),
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "messages": formatted_messages,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_messages": total_messages,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error in chat_history: {str(e)}", exc_info=True)
        return JsonResponse({
            "error": str(e),
            "success": False
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_session(request, session_id):
    """
    Delete a chat session and all its messages
    
    DELETE /chat/session/<session_id>/
    
    Returns:
    {
        "message": "Session deleted successfully",
        "session_id": "uuid",
        "deleted_messages": 10,
        "success": true
    }
    """
    try:
        # Get session
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return JsonResponse({
                "error": "Session not found",
                "success": False
            }, status=404)
        
        # Count messages before deletion
        message_count = ChatHistory.objects.filter(session=session).count()
        
        # Delete the session (CASCADE will delete all ChatHistory records)
        session_id_str = str(session.session_id)
        session.delete()
        
        return JsonResponse({
            "message": "Session deleted successfully",
            "session_id": session_id_str,
            "deleted_messages": message_count,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error in delete_session: {str(e)}", exc_info=True)
        return JsonResponse({
            "error": str(e),
            "success": False
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint to verify the service is running
    """
    from .models import Document
    
    try:
        doc_count = Document.objects.count()
        return JsonResponse({
            "status": "healthy",
            "documents_count": doc_count,
            "success": True
        })
    except Exception as e:
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e),
            "success": False
        }, status=500)
