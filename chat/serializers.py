"""
REST API serializers for Chat
"""
from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat session"""
    session_id = serializers.UUIDField(read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ['session_id', 'is_public', 'is_active', 'created_at', 'last_activity']
        read_only_fields = ['session_id', 'created_at', 'last_activity']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for individual chat messages"""
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'timestamp', 'retrieved_documents']
        read_only_fields = ['id', 'timestamp']


class ChatHistorySerializer(serializers.Serializer):
    """Serializer for paginated chat history response"""
    session_id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    last_activity = serializers.DateTimeField()
    messages = ChatMessageSerializer(many=True)
    pagination = serializers.DictField()
