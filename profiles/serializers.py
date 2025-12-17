from rest_framework import serializers
from .models import Resume

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ('id', 'original_filename', 'uploaded_at', 'file')
        read_only_fields = ('id', 'original_filename', 'uploaded_at', 'file')
