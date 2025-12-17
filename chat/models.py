from django.db import models
from pgvector.django import VectorField
import uuid


class Document(models.Model):
    """
    Model to store portfolio information with vector embeddings for RAG.
    Each document represents a piece of information about you (skills, projects, experience, etc.)
    """
    text = models.TextField(help_text="The actual content/information")
    embedding = VectorField(dimensions=768, help_text="Vector embedding (Google text-embedding-004)")
    
    # Metadata fields
    category = models.CharField(
        max_length=100, 
        help_text="Category: skills, projects, experience, education, about, etc.",
        db_index=True
    )
    source = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Source of the information (e.g., resume, LinkedIn, etc.)"
    )
    title = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Title or heading for this information"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.category}: {self.title or self.text[:50]}"


class ChatSession(models.Model):
    """
    Model to track WebSocket chat sessions
    """
    session_id = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        help_text="Unique session identifier"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Optional metadata
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['is_active', 'last_activity']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id} - {self.created_at}"


class ChatHistory(models.Model):
    """
    Store individual chat messages within sessions
    """
    session = models.ForeignKey(
        ChatSession, 
        on_delete=models.CASCADE, 
        related_name='messages',
        help_text="Associated chat session"
    )
    user_query = models.TextField()
    bot_response = models.TextField()
    retrieved_documents = models.JSONField(default=list, help_text="IDs of documents used for response")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']  # Chronological order within session
        verbose_name_plural = "Chat histories"
        indexes = [
            models.Index(fields=['session', 'timestamp']),
        ]
    
    def __str__(self):
        return f"[{self.session.session_id}] {self.user_query[:50]}"
