from datetime import timedelta

from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def chat_day_heading(value):
    """Today / Yesterday / 'Monday, April 7, 2026' for message date separators."""
    if not value:
        return ""
    dt = timezone.localtime(value)
    d = dt.date()
    today = timezone.localdate()
    if d == today:
        return "Today"
    if d == today - timedelta(days=1):
        return "Yesterday"
    weekday = dt.strftime("%A")
    return f"{weekday}, {dt.strftime('%B')} {d.day}, {d.year}"
