from django.urls import path
from .views import (
    SignupView, 
    LoginView, 
    GoogleOAuthStartView, 
    GoogleOAuthCallbackView, 
    RefreshView, 
    LogoutView, 
    UserMeView
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', RefreshView.as_view(), name='token_refresh'), 
    path('google/', GoogleOAuthStartView.as_view(), name='google_oauth_start'),
    path('google/callback/', GoogleOAuthCallbackView.as_view(), name='google_oauth_callback'),
    path('me/', UserMeView.as_view(), name='auth_me'),
]
