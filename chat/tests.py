"""
Unit tests for Chat application
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import RAGDocument, ChatSession, ChatMessage

User = get_user_model()


class RAGDocumentModelTest(TestCase):
    """Test RAGDocument model and user isolation"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@test.com', password='test123')
        self.user2 = User.objects.create_user(email='user2@test.com', password='test123')
    
    def test_document_belongs_to_user(self):
        """Test that documents are properly associated with users"""
        doc = RAGDocument.objects.create(
            user=self.user1,
            title="Test Doc",
            text="Test content",
            section="bio",
            embedding=[0.1] * 768
        )
        self.assertEqual(doc.user_id, self.user1.id)
    
    def test_user_isolation_query(self):
        """Test that user queries are properly isolated"""
        RAGDocument.objects.create(
            user=self.user1,
            title="User1 Doc",
            text="Content for user 1",
            section="bio",
            embedding=[0.1] * 768
        )
        RAGDocument.objects.create(
            user=self.user2,
            title="User2 Doc",
            text="Content for user 2",
            section="bio",
            embedding=[0.2] * 768
        )
        
        # User 1 should only see their own documents
        user1_docs = RAGDocument.objects.filter(user=self.user1)
        self.assertEqual(user1_docs.count(), 1)
        self.assertEqual(user1_docs.first().title, "User1 Doc")
        
        # User 2 should only see their own documents
        user2_docs = RAGDocument.objects.filter(user=self.user2)
        self.assertEqual(user2_docs.count(), 1)
        self.assertEqual(user2_docs.first().title, "User2 Doc")


class ChatSessionModelTest(TestCase):
    """Test ChatSession model"""
    
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.com', password='test123')
    
    def test_session_creation(self):
        """Test session is created with UUID"""
        session = ChatSession.objects.create(
            user=self.user,
            is_public=False
        )
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.user_id, self.user.id)
        self.assertFalse(session.is_public)
    
    def test_public_session(self):
        """Test public session flag"""
        session = ChatSession.objects.create(
            user=self.user,
            is_public=True
        )
        self.assertTrue(session.is_public)


class ChatMessageModelTest(TestCase):
    """Test ChatMessage model"""
    
    def setUp(self):
        self.user = User.objects.create_user(email='test@test.com', password='test123')
        self.session = ChatSession.objects.create(user=self.user)
    
    def test_message_creation(self):
        """Test message creation with roles"""
        user_msg = ChatMessage.objects.create(
            session=self.session,
            role='user',
            content='Hello'
        )
        assistant_msg = ChatMessage.objects.create(
            session=self.session,
            role='assistant',
            content='Hi there!'
        )
        
        self.assertEqual(user_msg.role, 'user')
        self.assertEqual(assistant_msg.role, 'assistant')
    
    def test_message_ordering(self):
        """Test messages are ordered by timestamp"""
        ChatMessage.objects.create(session=self.session, role='user', content='First')
        ChatMessage.objects.create(session=self.session, role='assistant', content='Second')
        ChatMessage.objects.create(session=self.session, role='user', content='Third')
        
        messages = list(self.session.messages.all())
        self.assertEqual(messages[0].content, 'First')
        self.assertEqual(messages[1].content, 'Second')
        self.assertEqual(messages[2].content, 'Third')


class CreateSessionAPITest(APITestCase):
    """Test session creation API"""
    
    def setUp(self):
        from profiles.models import Portfolio
        
        self.user = User.objects.create_user(email='test@test.com', password='test123')
        self.portfolio = Portfolio.objects.create(user=self.user, title='Test Portfolio')
    
    def test_create_session_authenticated(self):
        """Test authenticated user can create session"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/chat/session/')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('session_id', response.data)
        self.assertFalse(response.data['is_public'])
    
    def test_create_session_unauthenticated(self):
        """Test unauthenticated request is rejected"""
        response = self.client.post('/api/chat/session/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChatHistoryAPITest(APITestCase):
    """Test chat history API"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@test.com', password='test123')
        self.user2 = User.objects.create_user(email='user2@test.com', password='test123')
        
        self.session = ChatSession.objects.create(user=self.user1, is_public=False)
        ChatMessage.objects.create(session=self.session, role='user', content='Hello')
        ChatMessage.objects.create(session=self.session, role='assistant', content='Hi!')
    
    def test_owner_can_access_history(self):
        """Test session owner can access history"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(f'/api/chat/history/{self.session.session_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['messages']), 2)
    
    def test_non_owner_cannot_access_private_session(self):
        """Test non-owner cannot access private session"""
        self.client.force_authenticate(user=self.user2)
        
        response = self.client.get(f'/api/chat/history/{self.session.session_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_public_session_accessible(self):
        """Test public session is accessible without auth"""
        public_session = ChatSession.objects.create(user=self.user1, is_public=True)
        ChatMessage.objects.create(session=public_session, role='user', content='Public hello')
        
        response = self.client.get(f'/api/chat/history/{public_session.session_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
