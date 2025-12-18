from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .serializers import SignupSerializer, GoogleAuthSerializer, UserSerializer

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

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            # In serializer we verified the token and returned the ID content as the value of 'id_token'
            id_info = serializer.validated_data['id_token']
            email = id_info.get('email')
            
            # Extract fields as per requirement
            name = id_info.get('name', '')
            given_name = id_info.get('given_name', '')
            family_name = id_info.get('family_name', '')
            picture = id_info.get('picture', '')

            if not email:
                return Response(
                    {'error': 'Email not found in Google token'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if user exists
            user = User.objects.filter(email=email).first()
            
            if user:
                # Login existing user
                pass
            else:
                 # Create new user
                 user = User.objects.create_user(
                    email=email,
                    password=None,
                    name=name
                )
            
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "Google login successful",
                "user": {
                    "email": user.email, 
                    "name": user.name,
                    "picture": picture 
                },
                "tokens": tokens
            })
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
