from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Resume(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resume')
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='resumes/')
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
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

class TechRegistry(models.Model):
    ICON_TYPE_CHOICES = [
        ('svg', 'SVG'),
        ('png', 'PNG'),
        ('url', 'URL'),
        ('iconify', 'Iconify'),
    ]
    COLOR_VARIANT_CHOICES = [
        ('colored', 'Colored'),
        ('black', 'Black'),
        ('white', 'White'),
    ]

    display_name = models.CharField(max_length=100)
    code_name = models.CharField(max_length=100, unique=True, help_text="Used in bio like {{code_name}}")
    icon_type = models.CharField(max_length=20, choices=ICON_TYPE_CHOICES, default='url')
    icon_path = models.FileField(upload_to='tech_icons/', blank=True, null=True, help_text="Stored file path for SVG/PNG")
    icon_source_url = models.URLField(blank=True, null=True, help_text="Where icon was fetched from")
    doc_url = models.URLField(blank=True, null=True)
    color_variant = models.CharField(max_length=20, choices=COLOR_VARIANT_CHOICES, default='colored')
    
    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        self.code_name = self.code_name.lower().replace(' ', '-')
        super().save(*args, **kwargs)

class SocialRegistry(models.Model):
    ICON_TYPE_CHOICES = [
        ('svg', 'SVG'),
        ('png', 'PNG'),
        ('url', 'URL'),
        ('iconify', 'Iconify'),
    ]
    COLOR_VARIANT_CHOICES = [
        ('colored', 'Colored'),
        ('black', 'Black'),
        ('white', 'White'),
    ]

    display_name = models.CharField(max_length=100, help_text="Display name (e.g., 'GitHub', 'LinkedIn')")
    code_name = models.CharField(max_length=100, unique=True, help_text="Used as key (e.g., 'github', 'linkedin')")
    icon_type = models.CharField(max_length=20, choices=ICON_TYPE_CHOICES, default='url')
    icon_path = models.FileField(upload_to='social_icons/', blank=True, null=True, help_text="Stored file path for SVG/PNG")
    icon_source_url = models.URLField(blank=True, null=True, help_text="Where icon was fetched from")
    color_variant = models.CharField(max_length=20, choices=COLOR_VARIANT_CHOICES, default='colored')
    
    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Social Platform"
        verbose_name_plural = "Social Platforms"

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        self.code_name = self.code_name.lower().replace(' ', '-')
        super().save(*args, **kwargs)
