from django.urls import path
from chat.views import chat_history, delete_session, health_check

urlpatterns = [
    path("chat/history/<uuid:session_id>/", chat_history, name="chat_history"),
    path("chat/session/<uuid:session_id>/", delete_session, name="delete_session"),
    path("health/", health_check, name="health_check"),
]
