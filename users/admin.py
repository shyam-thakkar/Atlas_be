from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active')
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
        ('Personal info', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
