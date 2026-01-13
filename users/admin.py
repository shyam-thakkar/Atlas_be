from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'user_tier', 'plan_type', 'subscription_expiry', 'authentication_method', 'resume_process_count', 'username_change_count', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active', 'user_tier', 'plan_type', 'authentication_method')
    list_filter = ('is_staff', 'is_active', 'user_tier', 'authentication_method')
    search_fields = ('email', 'name')
    ordering = ('email',)
    
    # Since we use email as username, we need to adjust fieldsets if we were using the full BaseUserAdmin,
    # but for a quick start, we can just specify the ordering and basics.
    # BaseUserAdmin expects a 'username' field usually, so we might need to be careful.
    # Actually, simpler is to just inherit from admin.ModelAdmin if we don't need the extensive permission sets UI of BaseUserAdmin immediately,
    # OR we override the fieldsets to remove username.
    
    # Let's try to be robust:
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'google_id')}),
        ('Subscription', {'fields': ('user_tier', 'plan_type', 'subscription_expiry')}),
        ('Account', {'fields': ('authentication_method', 'resume_process_count', 'username_change_count')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    readonly_fields = ('created_at', 'last_login', 'google_id')

