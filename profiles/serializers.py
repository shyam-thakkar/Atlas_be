from rest_framework import serializers
from .models import Resume, TechRegistry, SocialRegistry

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ('id', 'original_filename', 'uploaded_at', 'file')
        read_only_fields = ('id', 'original_filename', 'uploaded_at', 'file')

class TechRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TechRegistry
        fields = [
            'id', 'display_name', 'code_name', 'icon_type', 
            'icon_path', 'icon_source_url', 'doc_url', 
            'color_variant', 'is_verified'
        ]
        read_only_fields = ['id', 'is_verified', 'icon_path']

class SocialRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialRegistry
        fields = [
            'id', 'display_name', 'code_name', 'icon_type',
            'icon_path', 'icon_source_url',
            'color_variant', 'is_verified'
        ]
        read_only_fields = ['id', 'is_verified', 'icon_path']
