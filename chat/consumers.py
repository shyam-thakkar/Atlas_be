"""
WebSocket Consumer for Multi-Tenant Portfolio Chatbot
Handles real-time chat with session management and user isolation
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from asgiref.sync import sync_to_async

from .models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chat with strict user isolation.
    
    Connection URL: /ws/chat/<session_id>/
    
    For dashboard (authenticated):
        - JWT token validated
        - Session must belong to authenticated user
    
    For public chat:
        - Session must be marked as is_public=True
        - Read-only portfolio access
    """
    
    async def connect(self):
        """Handle WebSocket connection with session validation"""
        try:
            # Get session_id from URL
            self.session_id = self.scope['url_route']['kwargs'].get('session_id')
            
            if not self.session_id:
                logger.warning("WebSocket connection without session_id")
                await self.close()
                return
            
            # Validate session exists
            self.session = await self.get_session(self.session_id)
            
            if not self.session:
                logger.warning(f"Session not found: {self.session_id}")
                await self.close()
                return
            
            # For non-public sessions, verify authentication
            if not self.session.is_public:
                user = self.scope.get('user')
                if not user or not user.is_authenticated:
                    logger.warning(f"Unauthenticated access to private session: {self.session_id}")
                    await self.close()
                    return
                
                # Verify session belongs to this user
                if user.id != self.session.user_id:
                    logger.warning(f"User {user.id} attempted to access session owned by {self.session.user_id}")
                    await self.close()
                    return
            
            # Initialize RAG service for this user
            self.rag_service = await self.init_rag_service(self.session.user_id)
            
            # Accept connection
            await self.accept()
            
            # Load recent chat history for context
            self.chat_history = await self.load_recent_messages(limit=10)
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'session_info',
                'session_id': str(self.session.session_id),
                'is_public': self.session.is_public,
                'message': 'Connected successfully',
                'history_loaded': len(self.chat_history)
            }))
            
            logger.info(f"WebSocket connected: Session {self.session.session_id}")
            
        except Exception as e:
            logger.error(f"Error in connect: {e}", exc_info=True)
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'session'):
            await self.update_session_activity()
            logger.info(f"WebSocket disconnected: Session {self.session.session_id}")
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'query')
            
            if message_type == 'query':
                await self.handle_query(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            elif message_type == 'history':
                await self.handle_history_request(data)
            else:
                await self.send_error(f'Unknown message type: {message_type}')
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON')
        except Exception as e:
            logger.error(f"Error in receive: {e}", exc_info=True)
            await self.send_error("Failed to process message")
    
    async def handle_query(self, data):
        """Process a chat query"""
        query = data.get('query', '').strip()
        
        if not query:
            await self.send_error('Query is required')
            return
        
        # Optional parameters
        top_k = min(data.get('top_k', 5), 10)  # Max 10
        section = data.get('section')
        
        # Send typing indicator
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'message': 'Thinking...'
        }))
        
        # Save user message
        await self.save_message(role='user', content=query)
        
        # Process query with RAG
        result = await self.process_rag_query(
            query=query,
            top_k=top_k,
            section=section
        )
        
        # Save assistant response
        await self.save_message(
            role='assistant',
            content=result.get('response', ''),
            doc_ids=result.get('doc_ids', [])
        )
        
        # Update session activity
        await self.update_session_activity()
        
        # Send response
        await self.send(text_data=json.dumps({
            'type': 'response',
            'query': query,
            'response': result.get('response'),
            'sources': result.get('sources', []),
            'success': result.get('success', False),
            'timestamp': timezone.now().isoformat()
        }))
    
    async def handle_history_request(self, data):
        """Send chat history to client"""
        limit = min(data.get('limit', 20), 50)  # Max 50
        messages = await self.load_recent_messages(limit=limit)
        
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': messages
        }))
    
    async def send_error(self, error_message):
        """Send error response"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': error_message
        }))
    
    # Database operations
    
    @database_sync_to_async
    def get_session(self, session_id):
        """Get session by ID"""
        try:
            return ChatSession.objects.select_related('user', 'portfolio').get(
                session_id=session_id,
                is_active=True
            )
        except ChatSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def init_rag_service(self, user_id):
        """Initialize RAG service for user"""
        from .services import RAGService
        return RAGService(user_id=user_id)
    
    @database_sync_to_async
    def load_recent_messages(self, limit=10):
        """Load recent messages for context"""
        messages = ChatMessage.objects.filter(
            session=self.session
        ).order_by('-timestamp')[:limit]
        
        # Return in chronological order
        return [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in reversed(list(messages))
        ]
    
    @database_sync_to_async
    def save_message(self, role, content, doc_ids=None):
        """Save a chat message"""
        ChatMessage.objects.create(
            session=self.session,
            role=role,
            content=content,
            retrieved_documents=doc_ids or []
        )
        
        # Update chat history for context
        self.chat_history.append({
            'role': role,
            'content': content
        })
        # Keep only last 10
        self.chat_history = self.chat_history[-10:]
    
    @database_sync_to_async
    def update_session_activity(self):
        """Update session last activity"""
        self.session.last_activity = timezone.now()
        self.session.save(update_fields=['last_activity'])
    
    @database_sync_to_async
    def process_rag_query(self, query, top_k=5, section=None):
        """Process query with RAG service"""
        try:
            return self.rag_service.process_query(
                query=query,
                top_k=top_k,
                section=section,
                chat_history=self.chat_history
            )
        except Exception as e:
            logger.error(f"RAG query error: {e}", exc_info=True)
            return {
                'response': "I'm having trouble processing your question. Please try again.",
                'sources': [],
                'success': False,
                'doc_ids': []
            }
