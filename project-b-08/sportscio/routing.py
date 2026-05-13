# Description: WebSocket routing for the Sportscio Django app, defining URL patterns for real-time chat and announcement features using Django Channels.

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/announcements/$', consumers.AnnouncementConsumer.as_asgi()),
]
