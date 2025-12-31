"""
WebSocket URL routing for chat application
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Session-based WebSocket endpoint
    # URL: /ws/chat/<session_id>/
    re_path(
        r'ws/chat/(?P<session_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$',
        consumers.ChatConsumer.as_asgi()
    ),
]
