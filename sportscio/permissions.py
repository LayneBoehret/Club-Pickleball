"""App-level roles: member, club leader, user_admin.

Club leaders can upload documents, post announcements, and manage events.
User administrators may only manage role assignments and cannot use app features.
"""
from .models import Profile


def _profile(user):
    if not user.is_authenticated:
        return None
    try:
        return user.profile
    except Profile.DoesNotExist:
        return None


def is_officer(user):
    p = _profile(user)
    return p is not None and p.role == Profile.ROLE_OFFICER


def is_user_admin(user):
    p = _profile(user)
    return p is not None and p.role == Profile.ROLE_USER_ADMIN


def is_member(user):
    p = _profile(user)
    return p is not None and p.role == Profile.ROLE_MEMBER


def is_privileged(user):
    """Club leader tools + Django superuser (same UI shell for now)."""
    return is_officer(user) or (user.is_authenticated and user.is_superuser)
