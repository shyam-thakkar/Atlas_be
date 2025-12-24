from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

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


class Username(models.Model):
    """
    Global username registry. Each username can only be owned by one user.
    Username can be changed based on tier limits.
    """
    username = models.CharField(
        max_length=50, 
        unique=True, 
        db_index=True,
        help_text="Lowercase, URL-safe username (e.g., 'johndoe')"
    )
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='portfolio_username'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['username']),
        ]
    
    def __str__(self):
        return f"{self.username} -> {self.user.email}"


class ReservedUsername(models.Model):
    """
    Usernames that cannot be claimed by users.
    E.g., 'admin', 'api', 'www', 'support', etc.
    """
    username = models.CharField(max_length=50, unique=True, db_index=True)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Reserved Username"
        verbose_name_plural = "Reserved Usernames"
    
    def __str__(self):
        return self.username


class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    title = models.CharField(max_length=255, default="My Portfolio")
    theme = models.CharField(max_length=50, default='default')
    # Username for public URL - OneToOne because one portfolio per user
    username = models.OneToOneField(
        'Username',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='portfolio',
        help_text="Claimed username for public URL (e.g., username.aifolio.in)"
    )
    missing_tech_stack = models.JSONField(default=list, blank=True, help_text="List of tech names not found in Registry")
    contact_data = models.JSONField(default=dict, blank=True, help_text="Contact section data: message, cta_text")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_published(self):
        """Portfolio is published if it has an active snapshot."""
        return self.published_snapshots.filter(is_active=True).exists()
    
    @property
    def public_url(self):
        """Returns the public URL for this portfolio if username is claimed."""
        from django.conf import settings
        if self.username:
            # PORTFOLIO_URL_TEMPLATE should be like:
            # Production: "https://{username}.aifolio.in"
            # Development: "http://localhost:3000/portfolio/{username}"
            template = getattr(settings, 'PORTFOLIO_URL_TEMPLATE', 'http://localhost:3000/portfolio/{username}')
            return template.format(username=self.username.username)
        return None
    
    @property
    def active_snapshot(self):
        """Returns the currently active published snapshot, or None."""
        return self.published_snapshots.filter(is_active=True).first()

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class PublishedSnapshot(models.Model):
    """
    Immutable snapshot of a portfolio at publish time.
    Only the latest active snapshot is public; older ones are kept for history/rollback.
    """
    portfolio = models.ForeignKey(
        Portfolio, 
        on_delete=models.CASCADE, 
        related_name='published_snapshots'
    )
    version = models.PositiveIntegerField(default=1)
    snapshot_data = models.JSONField(
        help_text="Complete serialized portfolio state at publish time"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="True for the currently public version"
    )
    published_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['portfolio', 'is_active']),
        ]
        constraints = [
            # Ensure only one active snapshot per portfolio
            models.UniqueConstraint(
                fields=['portfolio'],
                condition=models.Q(is_active=True),
                name='unique_active_snapshot_per_portfolio'
            )
        ]
    
    def __str__(self):
        return f"{self.portfolio} v{self.version} ({'active' if self.is_active else 'archived'})"


class Media(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('logo', 'Logo'),
    ]
    owner_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    owner_object_id = models.PositiveIntegerField()
    owner = GenericForeignKey('owner_content_type', 'owner_object_id')
    
    file = models.FileField(upload_to='media_assets/')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default='image')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.media_type} for {self.owner}"

class CompanyRegistry(models.Model):
    name = models.CharField(max_length=255)
    domain = models.URLField(blank=True, null=True, help_text="e.g. google.com, used for logo fetching")
    logo_file = models.ImageField(upload_to='company_registry_logos/', null=True, blank=True)
    logo_url = models.URLField(blank=True, null=True)
    
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Company Registry"
        ordering = ['name']
        
    def __str__(self):
        return self.name

class PortfolioProfile(models.Model):
    portfolio = models.OneToOneField(Portfolio, on_delete=models.CASCADE, related_name='profile')
    headline = models.CharField(max_length=255, blank=True, default='')
    short_bio = models.TextField(blank=True, default='')
    long_bio = models.TextField(blank=True, default='')
    
    def __str__(self):
        return f"Profile for {self.portfolio}"

class PortfolioTech(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='tech_stack')
    tech = models.ForeignKey(TechRegistry, on_delete=models.CASCADE)
    proficiency = models.CharField(max_length=50, blank=True, help_text="e.g. Expert, Intermediate")
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.tech.display_name} ({self.proficiency})"

class PortfolioExperience(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='experiences')
    company = models.ForeignKey(CompanyRegistry, on_delete=models.SET_NULL, null=True, blank=True)
    company_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True, max_length=255)
    
    # Media: Company logo can be accessed via Media generic relation
    
    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.role} at {self.company_name}"
        
    def save(self, *args, **kwargs):
        if self.company and not self.company_name:
            self.company_name = self.company.name
        super().save(*args, **kwargs)

class PortfolioProject(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    repo_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    tech_used = models.ManyToManyField(TechRegistry, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    
    # New fields for rich project details
    key_features = models.JSONField(default=list, blank=True, help_text="List of key features")
    technical_challenges = models.JSONField(default=list, blank=True, help_text="List of technical challenges")
    year = models.CharField(max_length=24, blank=True, help_text="Year of completion (e.g., '2024')")
    project_type = models.CharField(max_length=100, blank=True, help_text="e.g., 'Solo Project', 'Team Project'")
    thumbnail = models.ImageField(upload_to='project_thumbnails/', null=True, blank=True, help_text="Project screenshot/thumbnail")
    missing_technologies = models.JSONField(default=list, blank=True, help_text="List of tech names not found in Registry")

    # Media: Screenshots via Media generic relation

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title

class PortfolioEducation(models.Model):
    GRADE_TYPE_CHOICES = [
        ('cgpa', 'CGPA'),
        ('sgpa', 'SGPA'),
        ('percentage', 'Percentage'),
        ('gpa', 'GPA'),
        ('other', 'Other'),
    ]
    
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255, blank=True, help_text="e.g., Computer Science")
    grade = models.CharField(max_length=20, blank=True, help_text="e.g., 8.5, 85%, 3.8")
    grade_type = models.CharField(max_length=20, choices=GRADE_TYPE_CHOICES, blank=True, help_text="Type of grading system")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.degree} at {self.institution}"

class PortfolioSocial(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='socials')
    social_platform = models.ForeignKey(SocialRegistry, on_delete=models.CASCADE)
    url = models.URLField()
    
    def __str__(self):
        return f"{self.social_platform.display_name}: {self.url}"

class PortfolioAISnapshot(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='ai_snapshots')
    raw_resume_text = models.TextField(blank=True)
    extracted_jsonb = models.JSONField()
    model_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Snapshot {self.id} for {self.portfolio}"
