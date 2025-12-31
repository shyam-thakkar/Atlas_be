from django.contrib import admin
from .models import RAGDocument, ChatSession, ChatMessage


@admin.register(RAGDocument)
class RAGDocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'section', 'title', 'portfolio_version', 'created_at']
    list_filter = ['section', 'portfolio_version', 'created_at']
    search_fields = ['title', 'text', 'user__email']
    readonly_fields = ['embedding', 'created_at', 'updated_at']
    raw_id_fields = ['user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'is_public', 'is_active', 'created_at', 'last_activity']
    list_filter = ['is_public', 'is_active', 'created_at']
    search_fields = ['session_id', 'user__email']
    readonly_fields = ['session_id', 'created_at', 'last_activity']
    raw_id_fields = ['user', 'portfolio']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'portfolio')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_session_id', 'role', 'content_preview', 'timestamp']
    list_filter = ['role', 'timestamp']
    search_fields = ['content', 'session__session_id']
    readonly_fields = ['timestamp']
    raw_id_fields = ['session']
    
    def get_session_id(self, obj):
        return str(obj.session.session_id)[:8] + '...'
    get_session_id.short_description = 'Session'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session')
