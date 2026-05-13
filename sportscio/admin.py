# AI Use: Generated with Gemini 3 Flash on 2026-04-24.
# Prompt: "Configure admin.py to manage Profile, ClubDocument, Message, and Announcement models with search filters and custom fieldsets".
# Notes: Configures the backend interface for model management and includes a save_model override for Announcements.
from django.contrib import admin
from .models import ClubDocument, Profile, Message, Announcement


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'birthday')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


@admin.register(ClubDocument)
class ClubDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "uploaded_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "uploaded_by__username")
    readonly_fields = ("created_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'timestamp')
    list_filter = ('room', 'timestamp')
    search_fields = ('sender__username', 'content')
    ordering = ['-timestamp']
    readonly_fields = ('timestamp',)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    ordering = ['-created_at']
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'content')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('author', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)
