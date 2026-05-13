# AI Use: Generated with Gemini 3 Flash on 2026-04-01.
# Prompt: "Define Django models for Profile, Message, Announcement, ClubDocument, and Event with appropriate foreign keys and choices".
# Notes: Establishes the core data structure including user roles, S3-ready image fields, and timestamped messaging.

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    ROLE_MEMBER = "member"
    ROLE_OFFICER = "officer"
    ROLE_USER_ADMIN = "user_admin"

    ROLE_CHOICES = (
        (ROLE_MEMBER, "Member"),
        (ROLE_OFFICER, "Club leader"),
        (ROLE_USER_ADMIN, "User administrator"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    birthday = models.DateField(null=True, blank=True)
    avatar = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
        help_text="Profile photo; stored in S3 in production.",
    )
    
    email_notifications = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    room = models.CharField(max_length=100, default='general')

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

class Announcement(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class ClubDocument(models.Model):
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="club_documents")
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="documents/%Y/%m/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class Event(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True, default="")
    event_type = models.CharField(max_length=32, blank=True, default="")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return self.title