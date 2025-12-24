from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    TIER_CHOICES = [
        ('beta', 'Beta'),
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    # Tier limits for resume processing
    TIER_LIMITS = {
        'beta': 5,
        'free': 3,
        'pro': 50,
        'enterprise': -1,  # Unlimited
    }
    
    # Tier limits for username changes
    USERNAME_CHANGE_LIMITS = {
        'beta': 1,
        'free': 2,
        'pro': 5,
        'enterprise': -1,  # Unlimited
    }
    
    AUTH_METHOD_CHOICES = [
        ('email', 'Email/Password'),
        ('google', 'Google'),
    ]
    
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    # Account fields
    user_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='beta')
    authentication_method = models.CharField(max_length=20, choices=AUTH_METHOD_CHOICES, default='email')
    resume_process_count = models.PositiveIntegerField(default=0, help_text="Number of times user has processed a resume")
    username_change_count = models.PositiveIntegerField(default=0, help_text="Number of times user has changed their portfolio username")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
    def get_resume_limit(self):
        """Returns the resume processing limit for the user's tier."""
        return self.TIER_LIMITS.get(self.user_tier, 3)
    
    def can_process_resume(self):
        """Check if user can process another resume based on their tier limit."""
        limit = self.get_resume_limit()
        if limit == -1:  # Unlimited
            return True
        return self.resume_process_count < limit
    
    def increment_resume_count(self):
        """Increment the resume process count."""
        self.resume_process_count += 1
        self.save(update_fields=['resume_process_count'])
    
    def get_username_change_limit(self):
        """Returns the username change limit for the user's tier."""
        return self.USERNAME_CHANGE_LIMITS.get(self.user_tier, 1)
    
    def can_change_username(self):
        """Check if user can change their username based on tier limit."""
        limit = self.get_username_change_limit()
        if limit == -1:  # Unlimited
            return True
        return self.username_change_count < limit
    
    def get_remaining_username_changes(self):
        """Returns number of username changes remaining, or -1 for unlimited."""
        limit = self.get_username_change_limit()
        if limit == -1:
            return -1
        return max(0, limit - self.username_change_count)
    
    def increment_username_change_count(self):
        """Increment the username change count."""
        self.username_change_count += 1
        self.save(update_fields=['username_change_count'])

