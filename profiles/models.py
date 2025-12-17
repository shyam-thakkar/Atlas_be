from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Resume(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resume')
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='resumes/')
    extracted_text = models.TextField(blank=True)
    structured_data = models.JSONField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.original_filename}"

class ResumeProcessingStatus(models.Model):
    STATUS_CHOICES = [
        ('not_uploaded', 'Not Uploaded'),
        ('uploaded', 'Uploaded'),
        ('raw_extracting', 'Raw Extracting'),
        ('raw_extracted', 'Raw Extracted'),
        ('structure_extracting', 'Structure Extracting'),
        ('structure_extracted', 'Structure Extracted'),
        ('review_required', 'Review Required'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resume_status', db_index=True)
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='processing_status')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_uploaded')
    error_message = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.status}"
