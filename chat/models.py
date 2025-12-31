"""
Models for Multi-Tenant RAG Chatbot
Each model enforces user isolation through user_id foreign keys
"""
from django.db import models
from django.contrib.auth import get_user_model
from pgvector.django import VectorField
import uuid

User = get_user_model()


class RAGDocument(models.Model):
    """
    Vector storage for RAG with strict user isolation.
    Each document belongs to exactly one user.
    All queries MUST filter by user_id.
    """
    SECTION_CHOICES = [
        ('bio', 'Bio/About'),
        ('experience', 'Work Experience'),
        ('projects', 'Projects'),
        ('skills', 'Skills'),
        ('education', 'Education'),
        ('other', 'Other'),
    ]
    
    # User isolation - CRITICAL for multi-tenancy
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='rag_documents',
        db_index=True,
        help_text="Owner of this document - ALL queries must filter by this"
    )
    
    # Portfolio versioning for consistency
    portfolio_version = models.CharField(
        max_length=50, 
        blank=True, 
        default='',
        help_text="Version from PublishedSnapshot for versioned RAG"
    )
    
    # Content
    title = models.CharField(max_length=255, blank=True, help_text="Title/heading")
    text = models.TextField(help_text="The actual content for RAG")
    section = models.CharField(
        max_length=50, 
        choices=SECTION_CHOICES,
        db_index=True,
        help_text="Section type for filtered retrieval"
    )
    
    # Vector embedding (768 dimensions for Google text-embedding-004)
    embedding = VectorField(dimensions=768, help_text="Vector embedding")
    
    # Metadata
    source = models.CharField(max_length=255, blank=True, help_text="Source of info")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'section']),
            models.Index(fields=['user', 'portfolio_version']),
        ]
    
    def __str__(self):
        return f"[{self.user_id}] {self.section}: {self.title or self.text[:50]}"


class ChatSession(models.Model):
    """
    Chat session management with user isolation.
    Each session belongs to exactly one user's portfolio.
    """
    # Primary key
    session_id = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        db_index=True,
        help_text="Public session identifier"
    )
    
    # User isolation - session always belongs to portfolio owner
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_sessions',
        db_index=True,
        help_text="Portfolio owner (NOT the visitor)"
    )
    
    # Link to portfolio
    portfolio = models.ForeignKey(
        'profiles.Portfolio',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_sessions'
    )
    
    # Session type
    is_public = models.BooleanField(
        default=False, 
        help_text="True for public portfolio chat (read-only)"
    )
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_public', 'is_active']),
        ]
    
    def __str__(self):
        session_type = "public" if self.is_public else "dashboard"
        return f"{session_type} session {self.session_id} for user {self.user_id}"


class ChatMessage(models.Model):
    """
    Individual chat messages within a session.
    Stores both user queries and assistant responses.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    session = models.ForeignKey(
        ChatSession, 
        on_delete=models.CASCADE, 
        related_name='messages',
        help_text="Parent chat session"
    )
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES,
        help_text="Message sender role"
    )
    content = models.TextField(help_text="Message content")
    
    # Metadata for assistant messages
    retrieved_documents = models.JSONField(
        default=list, 
        blank=True,
        help_text="IDs of RAG documents used for response"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['session', 'timestamp']),
        ]
    
    def __str__(self):
        return f"[{self.session.session_id}] {self.role}: {self.content[:50]}"
