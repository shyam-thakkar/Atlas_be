"""
WebSocket Consumer for Portfolio Chatbot
Handles real-time chat with session management
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from urllib.parse import parse_qs

from .models import ChatSession, ChatHistory
from .rag_service import RAGService

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling chat messages
    
    Connection URL: ws://localhost:8000/ws/chat/?session_id=<optional-uuid>
    
    If session_id is provided, continues existing session
    If not provided, creates new session
    """
    
    async def connect(self):
        """
        Handle WebSocket connection
        """
        try:
            # Initialize RAG service once per connection (reuse for all queries)
            self.rag_service = await database_sync_to_async(RAGService)()
            
            # Parse query parameters
            query_string = self.scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            session_id_param = query_params.get('session_id', [None])[0]
            
            # Get or create session
            if session_id_param:
                # Try to continue existing session
                self.session = await self.get_or_create_session(session_id_param)
                is_new_session = False
            else:
                # Create new session
                self.session = await self.create_new_session()
                is_new_session = True
            
            # Accept WebSocket connection
            await self.accept()
            
            # Send session ID to client
            await self.send(text_data=json.dumps({
                'type': 'session_info',
                'session_id': str(self.session.session_id),
                'is_new_session': is_new_session,
                'message': 'Connected successfully'
            }))
            
            logger.info(f"WebSocket connected: Session {self.session.session_id}")
            
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}", exc_info=True)
            await self.close()
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        if hasattr(self, 'session'):
            await self.update_session_activity(self.session)
            logger.info(f"WebSocket disconnected: Session {self.session.session_id}")
    
    async def receive(self, text_data):
        """
        Handle incoming messages from WebSocket
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'query')
            
            if message_type == 'query':
                # Handle chat query
                query = data.get('query', '').strip()
                
                if not query:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'error': 'Query is required'
                    }))
                    return
                
                # Optional parameters
                top_k = data.get('top_k', 5)
                category = data.get('category')
                
                # Send typing indicator
                await self.send(text_data=json.dumps({
                    'type': 'typing',
                    'message': 'Thinking...'
                }))
                
                # Process query using RAG
                result = await self.process_query(
                    query=query,
                    top_k=top_k,
                    category=category
                )
                
                # Save to chat history
                await self.save_chat_history(
                    query=query,
                    response=result.get('response', ''),
                    doc_ids=result.get('doc_ids', [])
                )
                
                # Update session activity
                await self.update_session_activity(self.session)
                
                # Send response
                await self.send(text_data=json.dumps({
                    'type': 'response',
                    'query': query,
                    'response': result.get('response'),
                    'sources': result.get('sources', []),
                    'success': result.get('success', False),
                    'timestamp': timezone.now().isoformat()
                }))
            
            elif message_type == 'ping':
                # Handle ping for keeping connection alive
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
            
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'error': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}", exc_info=True)
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'I\'m not able to process your query',
                'details': str(e)
            }))
    
    @database_sync_to_async
    def create_new_session(self):
        """
        Create a new chat session
        """
        # Get client info from scope
        headers = dict(self.scope.get('headers', []))
        user_agent = headers.get(b'user-agent', b'').decode()
        
        # Get IP address
        client = self.scope.get('client', ['', ''])
        ip_address = client[0] if client else None
        
        session = ChatSession.objects.create(
            user_agent=user_agent,
            ip_address=ip_address
        )
        return session
    
    @database_sync_to_async
    def get_or_create_session(self, session_id):
        """
        Get existing session or create new one if not found
        """
        try:
            session = ChatSession.objects.get(session_id=session_id, is_active=True)
            return session
        except ChatSession.DoesNotExist:
            # Session not found, create new one
            return ChatSession.objects.create()
    
    @database_sync_to_async
    def update_session_activity(self, session):
        """
        Update session last activity timestamp
        """
        session.last_activity = timezone.now()
        session.save(update_fields=['last_activity'])
    
    @database_sync_to_async
    def save_chat_history(self, query, response, doc_ids):
        """
        Save chat message to history
        """
        ChatHistory.objects.create(
            session=self.session,
            user_query=query,
            bot_response=response,
            retrieved_documents=doc_ids
        )
    
    @database_sync_to_async
    def process_query(self, query, top_k=5, category=None):
        """
        Process query using RAG service (sync operation in async context)
        Reuses the RAGService instance created at connection time
        """
        try:
            result = self.rag_service.process_query(
                query=query,
                top_k=top_k,
                category=category
            )
            
            # Extract doc IDs for our history
            doc_ids = [source.get('id') for source in result.get('sources', []) if source.get('id')]
            result['doc_ids'] = doc_ids
            
            return result
            
        except Exception as e:
            logger.error(f"Error in process_query: {str(e)}", exc_info=True)
            return {
                'response': "I'm not able to process your query",
                'sources': [],
                'success': False,
                'doc_ids': []
            }
