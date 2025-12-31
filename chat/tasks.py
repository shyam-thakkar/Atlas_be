"""
Celery tasks for async RAG operations
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def rebuild_user_rag_documents(user_id: int, portfolio_version: str = "") -> dict:
    """
    Rebuild all RAG documents for a user asynchronously.
    
    This task should be triggered when:
    - Resume is uploaded and processed
    - Portfolio data is edited
    - Portfolio is published
    
    Args:
        user_id: The user ID to rebuild documents for
        portfolio_version: Optional version string
        
    Returns:
        Dict with status and count
    """
    try:
        from .services import RAGDocumentGenerator
        
        generator = RAGDocumentGenerator(user_id)
        count = generator.rebuild(portfolio_version=portfolio_version)
        
        logger.info(f"Rebuilt {count} RAG documents for user {user_id}")
        return {
            "success": True,
            "user_id": user_id,
            "documents_created": count
        }
        
    except Exception as e:
        logger.error(f"Failed to rebuild RAG documents for user {user_id}: {e}", exc_info=True)
        return {
            "success": False,
            "user_id": user_id,
            "error": str(e)
        }


@shared_task
def cleanup_inactive_sessions(days_old: int = 30) -> dict:
    """
    Clean up old inactive chat sessions.
    
    Args:
        days_old: Delete sessions older than this many days
        
    Returns:
        Dict with deleted count
    """
    from datetime import timedelta
    from django.utils import timezone
    from .models import ChatSession
    
    try:
        cutoff = timezone.now() - timedelta(days=days_old)
        deleted, _ = ChatSession.objects.filter(
            last_activity__lt=cutoff,
            is_active=False
        ).delete()
        
        logger.info(f"Cleaned up {deleted} old chat sessions")
        return {
            "success": True,
            "deleted_sessions": deleted
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
