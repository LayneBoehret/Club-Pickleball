# AI Use: Generated with Gemini 3 Flash on 2026-04-20.
# Prompt: "How do I authenticate Google SMPT on a Gmail account to send mass emails to a list of users?"
# Notes: Includes logic for unique username generation during social signups and offloads email sending to an asynchronous worker.

import os
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mass_mail
from background_task import background
from django_q.tasks import async_task  # <--- The Q2 worker hook
from allauth.account.signals import user_signed_up
from .models import Profile, Announcement, Event

def _make_unique_username(base: str) -> str:
    base = slugify(base or "")[:30].strip("-_") or "member"
    candidate = base
    i = 2
    while User.objects.filter(username=candidate).exists():
        suffix = f"-{i}"
        candidate = (base[: max(1, 30 - len(suffix))] + suffix).strip("-_")
        i += 1
    return candidate

@receiver(user_signed_up)
def set_username_on_social_signup(request, user, **kwargs):
    """
    Ensure username is always a clean, unique handle on first Google signup.
    Falls back to email local-part, then full name.
    """
    # allauth typically sets something, but it can be odd/blank depending on provider/user profile.
    current = (user.username or "").strip()
    email = (user.email or "").strip()
    base = ""

    if email and "@" in email:
        base = email.split("@", 1)[0]
    elif user.get_full_name().strip():
        base = user.get_full_name()
    else:
        base = current or "member"

    # If username is blank or looks email-ish, normalize it.
    if (not current) or ("@" in current) or (current.lower() in {"user", "member"}):
        user.username = _make_unique_username(base)
        user.save(update_fields=["username"])

def send_email_in_background(subject, message, from_email, recipient_list):
    """
    This function is now called by the Django Q worker process.
    """
    try:
        datatuple = tuple((subject, message, from_email, [email]) for email in recipient_list)
        send_mass_mail(datatuple, fail_silently=False)
    except Exception as e:
        print(f"Background SMTP Error: {e}")

@background(schedule=0)
def send_event_email(subject, message, from_email, recipient_list):
    try:
        datatuple = tuple((subject, message, from_email, [email]) for email in recipient_list)
        send_mass_mail(datatuple, fail_silently=False)
    except Exception as e:
        # On Heroku, this will show up in 'heroku logs --tail'
        print(f"Background SMTP Error: {e}")

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance, defaults={'role': Profile.ROLE_MEMBER})

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=Announcement)
def notify_members_new_announcement(sender, instance, created, **kwargs):
    if created:
        recipient_list = list(User.objects.filter(
            is_active=True,
            profile__email_notifications=True
        ).values_list('email', flat=True))

        recipient_list = [email for email in recipient_list if email]
        if not recipient_list:
            return

        author_name = instance.author.get_full_name() or instance.author.username
        subject = f"SportsCIO Announcement: {instance.title}"
        message = f"New announcement from {author_name}:\n\n{instance.title}\n\n{instance.content}"
        from_email = f"SportsCIO <{settings.DEFAULT_FROM_EMAIL}>"

        # Replace threading with async_task
        async_task(
            'sportscio.signals.send_email_in_background', # Path to the function
            subject, 
            message, 
            from_email, 
            recipient_list
        )

@receiver(post_save, sender=Event)
def notify_members_new_event(sender, instance, created, **kwargs):
    if created:
        recipient_list = list(User.objects.filter(
            is_active=True,
            profile__email_notifications=True
        ).values_list('email', flat=True))

        recipient_list = [email for email in recipient_list if email]
        if not recipient_list:
            return

        author_name = instance.created_by.get_full_name() or instance.created_by.username
        
        # Handle time formatting
        st = instance.start_time
        if isinstance(st, str):
            try:
                st = datetime.fromisoformat(st.replace('Z', '+00:00'))
            except ValueError:
                st = None

        if st and hasattr(st, 'strftime'):
            start_str = st.strftime("%B %d at %I:%M %p")
        else:
            start_str = str(instance.start_time)

        subject = f"New Event: {instance.title}"
        message = f"{author_name} added an event: {instance.title}\nWhen: {start_str}\n\n{instance.description}"
        from_email = f"SportsCIO <{settings.DEFAULT_FROM_EMAIL}>"

        # Replace threading with async_task
        async_task(
            'sportscio.signals.send_email_in_background', # Path to the function
            subject, 
            message, 
            from_email, 
            recipient_list
        )
