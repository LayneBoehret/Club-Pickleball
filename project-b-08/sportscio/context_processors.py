# AI Use: Generated with Gemini 3 Flash on 2026-03-20.
# Prompt: "Configure Django context processor so user profile roles and privileged status are available globally in templates".
# Notes: Provides boolean flags like is_officer and is_user_admin to all frontend templates.

from .models import Profile
from .permissions import is_privileged


def roles(request):
    if not request.user.is_authenticated:
        return {}
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return {
            "is_privileged": is_privileged(request.user),
            "is_officer": False,
            "is_user_admin": False,
        }
    return {
        "user_profile_obj": profile,
        "is_officer": profile.role == Profile.ROLE_OFFICER,
        "is_user_admin": profile.role == Profile.ROLE_USER_ADMIN,
        "is_privileged": is_privileged(request.user),
    }
