from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'created_at', 'profile_image', 'user_tier', 'plan_type', 'subscription_expiry', 'authentication_method', 'resume_process_count')
        read_only_fields = ('id', 'created_at', 'profile_image', 'user_tier', 'plan_type', 'subscription_expiry', 'authentication_method', 'resume_process_count')

    def get_profile_image(self, obj):
        try:
             if hasattr(obj, 'resume') and obj.resume.profile_photo:
                 request = self.context.get('request')
                 if request:
                      return request.build_absolute_uri(obj.resume.profile_photo.url)
                 return obj.resume.profile_photo.url
        except Exception:
             pass
        return None

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('email', 'password', 'name')

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name', '')
        )
        return user
