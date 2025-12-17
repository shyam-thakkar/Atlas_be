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
