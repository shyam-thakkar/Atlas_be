"""
REST API URL routing for chat application
"""
from django.urls import path
from . import views

urlpatterns = [
    # Session management
    path('session/', views.CreateSessionView.as_view(), name='chat-create-session'),
    path('session/public/<str:username>/', views.CreatePublicSessionView.as_view(), name='chat-create-public-session'),
    path('session/<uuid:session_id>/', views.DeleteSessionView.as_view(), name='chat-delete-session'),
    
    # Chat history
    path('history/<uuid:session_id>/', views.ChatHistoryView.as_view(), name='chat-history'),
    
    # RAG management
    path('rag/status/', views.RAGStatusView.as_view(), name='chat-rag-status'),
    path('rag/rebuild/', views.TriggerRAGRebuildView.as_view(), name='chat-rag-rebuild'),
]
