from django.contrib import admin
from .models import Document, ChatSession, ChatHistory


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    Admin interface for Document model
    """
    list_display = ['id', 'category', 'title', 'text_preview', 'created_at']
    list_filter = ['category', 'created_at', 'updated_at']
    search_fields = ['title', 'text', 'category', 'source']
    readonly_fields = ['created_at', 'updated_at', 'embedding']
    
    fieldsets = (
        ('Content', {
            'fields': ('text', 'category', 'title', 'source')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Embedding', {
            'fields': ('embedding',),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        """Show preview of text content"""
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
    text_preview.short_description = "Text Preview"


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for ChatSession model
    """
    list_display = ['session_id', 'created_at', 'last_activity', 'is_active', 'message_count']
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['session_id', 'ip_address']
    readonly_fields = ['session_id', 'created_at', 'last_activity']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('session_id', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_activity')
        }),
        ('Client Info', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def message_count(self, obj):
        """Show number of messages in this session"""
        return obj.messages.count()
    message_count.short_description = "Messages"


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for ChatHistory model
    """
    list_display = ['id', 'session_link', 'query_preview', 'timestamp', 'doc_count']
    list_filter = ['timestamp', 'session']
    search_fields = ['user_query', 'bot_response', 'session__session_id']
    readonly_fields = ['timestamp', 'retrieved_documents', 'session']
    
    fieldsets = (
        ('Session', {
            'fields': ('session',)
        }),
        ('Conversation', {
            'fields': ('user_query', 'bot_response')
        }),
        ('Metadata', {
            'fields': ('timestamp', 'retrieved_documents'),
            'classes': ('collapse',)
        }),
    )
    
    def session_link(self, obj):
        """Show session ID"""
        return str(obj.session.session_id)[:8] + "..."
    session_link.short_description = "Session"
    
    def query_preview(self, obj):
        """Show preview of user query"""
        return obj.user_query[:80] + "..." if len(obj.user_query) > 80 else obj.user_query
    query_preview.short_description = "Query"
    
    def doc_count(self, obj):
        """Show number of documents retrieved"""
        return len(obj.retrieved_documents)
    doc_count.short_description = "Docs Used"
