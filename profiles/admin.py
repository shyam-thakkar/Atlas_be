from django.contrib import admin
from .models import Resume, ResumeProcessingStatus

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'original_filename', 'uploaded_at')
    search_fields = ('user__email', 'original_filename')
    readonly_fields = ('uploaded_at',)

@admin.register(ResumeProcessingStatus)
class ResumeProcessingStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'updated_at')
    list_filter = ('status',)
    search_fields = ('user__email',)
    readonly_fields = ('updated_at',)

from .models import TechRegistry

@admin.register(TechRegistry)
class TechRegistryAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'code_name', 'icon_type', 'is_verified', 'created_at')
    list_filter = ('icon_type', 'is_verified', 'color_variant')
    search_fields = ('display_name', 'code_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('display_name',)

from .models import SocialRegistry

@admin.register(SocialRegistry)
class SocialRegistryAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'code_name', 'icon_type', 'is_verified', 'created_at')
    list_filter = ('icon_type', 'is_verified', 'color_variant')
    search_fields = ('display_name', 'code_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('display_name',)
