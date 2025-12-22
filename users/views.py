from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .serializers import SignupSerializer, UserSerializer

User = get_user_model()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "message": "User created successfully", 
                    "user": {"email": user.email, "name": user.name},
                    "tokens": tokens
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user:
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "Login successful", 
                "user": {"email": user.email, "name": user.name},
                "tokens": tokens
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class GoogleOAuthStartView(APIView):
    """
    Initiates Google OAuth flow by redirecting user to Google's authorization page.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        import secrets
        
        # Generate and store state for CSRF protection
        state = secrets.token_urlsafe(32)
        request.session["oauth_state"] = state

        # Build Google OAuth URL
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            "?response_type=code"
            f"&client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={settings.GOOGLE_CALLBACK_URL}"
            "&scope=openid email profile"
            f"&state={state}"
        )

        from django.shortcuts import redirect
        return redirect(google_auth_url)


class GoogleOAuthCallbackView(APIView):
    """
    Handles OAuth callback from Google, exchanges code for tokens,
    verifies ID token, creates/gets user, and redirects to frontend with JWT tokens.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        import requests
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        from django.shortcuts import redirect
        
        code = request.GET.get("code")
        state = request.GET.get("state")

        # Validate state for CSRF protection
        if not code or state != request.session.get("oauth_state"):
            return Response({"error": "Invalid OAuth state"}, status=status.HTTP_400_BAD_REQUEST)

        # Exchange authorization code for tokens
        try:
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_CALLBACK_URL,
                },
            ).json()

            id_token_str = token_response.get("id_token")
            
            if not id_token_str:
                return Response({"error": "No ID token received"}, status=status.HTTP_400_BAD_REQUEST)

            # Verify ID token
            id_info = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )

            google_id = id_info["sub"]
            email = id_info.get("email")

            if not email:
                return Response({"error": "Email not found in Google response"}, status=status.HTTP_400_BAD_REQUEST)

            # Get or create user based on google_id
            user, created = User.objects.get_or_create(
                google_id=google_id,
                defaults={
                    "email": email,
                    "name": id_info.get("name", ""),
                },
            )

            # Generate JWT tokens
            tokens = get_tokens_for_user(user)

            # Redirect to frontend with tokens in query params
            return redirect(
                f"{settings.FRONTEND_URL}/auth/google/callback"
                f"?access={tokens['access']}&refresh={tokens['refresh']}"
            )
            
        except Exception as e:
            return Response({"error": f"OAuth failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class RefreshView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "No refresh token provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh) 
            }
            
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # With stateless JWTs stored on the client, 'logout' is primarily a client-side action (deleting the token).
        # Optionally, we could blacklist the refresh token here if we wanted to enforce invalidation.
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            # Even if blacklist fails (e.g. token invalid), we return success for logout
            pass
            
        return Response({"message": "Logout successful"}, status=status.HTTP_204_NO_CONTENT)

class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
