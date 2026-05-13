# AI Use: Generated with Gemini 3 Flash on 2026-03-25.
# Prompt: "How do I implement a chat room and a separate consumer for broadcasting announcements using Django Channels?"
# Notes: Handles real-time communication logic, including database persistence for messages using database_sync_to_async.
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

chat_consumers = {}
announcement_consumers = []

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        if self.room_name not in chat_consumers:
            chat_consumers[self.room_name] = []
        chat_consumers[self.room_name].append(self)
        
        await self.accept()

    async def disconnect(self, close_code):
        if self.room_name in chat_consumers:
            if self in chat_consumers[self.room_name]:
                chat_consumers[self.room_name].remove(self)
            if not chat_consumers[self.room_name]:
                del chat_consumers[self.room_name]

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message')

        if message_content and self.user.is_authenticated:
            db_message = await self.save_message(message_content, self.room_name, self.user)
            avatar_url = await self.get_avatar_url(self.user)

            if self.room_name in chat_consumers:
                for consumer in chat_consumers[self.room_name]:
                    await consumer.send(text_data=json.dumps({
                        'type': 'chat_message',
                        'message': message_content,
                        'username': self.user.username,
                        'first_name': self.user.first_name,
                        'last_name': self.user.last_name,
                        'display_name': self.user.get_full_name() or self.user.username,
                        'avatar_url': avatar_url,
                        'timestamp': db_message.timestamp.isoformat(),
                        'user_id': self.user.id,
                    }))

    @database_sync_to_async
    def save_message(self, content, room, user):
        from .models import Message
        return Message.objects.create(sender=user, content=content, room=room)

    @database_sync_to_async
    def get_avatar_url(self, user):
        try:
            if hasattr(user, 'profile') and user.profile.avatar:
                return user.profile.avatar.url
        except:
            pass
        return None

class AnnouncementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        announcement_consumers.append(self)
        await self.accept()

    async def disconnect(self, close_code):
        if self in announcement_consumers:
            announcement_consumers.remove(self)

    async def announcement_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'announcement',
            'id': event['id'],
            'title': event['title'],
            'content': event['content'],
            'author': event['author'],
            'author_first_name': event.get('author_first_name', ''),
            'author_avatar_url': event.get('author_avatar_url'),
            'created_at': event['created_at'],
        }))