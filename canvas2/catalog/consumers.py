from asgiref.sync import async_to_sync
from django.core import serializers
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer, AsyncConsumer
from . import views
import json

# TODO: REMOVE REDUNDANT CONSUMERS, UPDATE WEBSOCKETS ON FRONT END

class IdeaConsumer(AsyncWebsocketConsumer):
    '''
    Consumer for websockets which are for modification of the Idea model
    '''
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['pk'] + "_tag"
        self.room_group_name = 'canvas_%s' %self.room_name
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        data = text_data_json['data']
        

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

    async def channel_message(self, event):
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'data': data
        }))


class CommentConsumer(AsyncWebsocketConsumer):
    '''
    Consumer for websockets which are for modification of the Comment model
    '''
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['pk'] + "_comment"
        self.room_group_name = 'canvas_%s' %self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        canvas_pk = self.scope['url_route']['kwargs']['pk']
        
        text_data_json = json.loads(text_data)
        data = text_data_json['data']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'channel_message',
                'data': data,
            }
        )

    async def channel_message(self, event):
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'data': data
        }))



class CollabConsumer(AsyncWebsocketConsumer):
    '''
    Consumer for websockets which are for modification of the User model
    '''
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['pk'] + "_collab"
        self.room_group_name = 'project_%s' %self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def receive(self, text_data):
        project_pk = self.scope['url_route']['kwargs']['pk']
        
        text_data_json = json.loads(text_data)
        data = text_data_json['data']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'channel_message',
                'data': data,
            }
        )


    async def channel_message(self, event):
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'data': data
        }))



class TagConsumer(AsyncWebsocketConsumer):
    '''
    Consumer for websockets which are for modification of the Tag model
    '''
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['pk'] + "_tag"
        self.room_group_name = 'project_%s' %self.room_name
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        project_pk = self.scope['url_route']['kwargs']['pk']

        text_data_json = json.loads(text_data)
        data = text_data_json['data']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'channel_message',
                'data': data,
            }
        )

    async def channel_message(self, event):
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'data': data
        }))