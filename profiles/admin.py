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
    list_display = ('display_name', 'code_name', 'icon_type', 'icon_path', 'is_verified', 'created_at')
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

from .models import (
    Portfolio, Media, PortfolioProfile, PortfolioTech, PortfolioExperience,
    PortfolioProject, PortfolioEducation, PortfolioSocial, PortfolioAISnapshot,
    CompanyRegistry
)

@admin.register(CompanyRegistry)
class CompanyRegistryAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('name', 'domain')
    readonly_fields = ('created_at', 'updated_at')

class PortfolioProfileInline(admin.StackedInline):
    model = PortfolioProfile
    can_delete = False

class PortfolioTechInline(admin.TabularInline):
    model = PortfolioTech
    extra = 1

class PortfolioExperienceInline(admin.StackedInline):
    model = PortfolioExperience
    extra = 0

class PortfolioProjectInline(admin.StackedInline):
    model = PortfolioProject
    extra = 0

class PortfolioEducationInline(admin.StackedInline):
    model = PortfolioEducation
    extra = 0

class PortfolioSocialInline(admin.TabularInline):
    model = PortfolioSocial
    extra = 1

class PortfolioAISnapshotInline(admin.StackedInline):
    model = PortfolioAISnapshot
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_published', 'created_at', 'updated_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('user__email', 'title')
    inlines = [
        PortfolioProfileInline,
        PortfolioTechInline,
        PortfolioExperienceInline,
        PortfolioProjectInline,
        PortfolioEducationInline,
        PortfolioSocialInline,
        PortfolioAISnapshotInline,
    ]

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('media_type', 'owner', 'created_at')
    list_filter = ('media_type', 'created_at')
    readonly_fields = ('created_at',)
