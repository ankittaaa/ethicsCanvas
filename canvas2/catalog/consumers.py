from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from . import views
import json


class IdeaConsumer(AsyncWebsocketConsumer):
    '''
    Consumer for websockets which are for modification of the Idea model
    '''
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['pk'] + "_idea"
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
        logged_in_user = self.scope['user']
        canvas_pk = self.scope['url_route']['kwargs']['pk']
        
        text_data_json = json.loads(text_data)
        function = text_data_json['function']
 

        if function == 'addIdea':
            '''
            ADDITION OF IDEA
            '''
            category = text_data_json['category']
            return_idea = views.new_idea(logged_in_user, canvas_pk, category)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'new_idea',
                    'function': function,
                    'idea': return_idea
                }
            )


        if function == 'modifyIdea':
            '''
            MODIFICATION OF IDEA
            '''
            input_text = text_data_json['input_text']
            idea_pk = text_data_json['idea_pk']
            i = text_data_json['i']
            
            print(i)

            return_idea = views.idea_detail(logged_in_user, idea_pk, input_text)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'modify_idea',
                    'function': function,
                    'idea': return_idea,
                    'i': i,
                }
            )


        if function == 'deleteIdea':
            '''
            DELETION OF IDEA
            '''
            idea_pk = text_data_json['idea_pk']
            i = text_data_json['i']

            category = views.delete_idea(logged_in_user, idea_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'delete_idea',
                    'function': function,
                    'i': i,
                    'category': category,
                }
            )


    async def new_idea(self, event):
        idea = event['idea']
        function = event['function']

        await self.send(text_data=json.dumps({
            'function': function,
            'idea': idea
        }))


    async def modify_idea(self, event):
        function = event['function']
        return_idea = event['idea']
        i = event['i']


        await self.send(text_data=json.dumps({
            'function': function,
            'idea': return_idea,
            'i': i
        }))
    

    async def delete_idea(self, event):
        i = event['i']
        function = event['function']
        category = event['category']

        await self.send(text_data=json.dumps({
            'function': function,
            'i': i,
            'category': category
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
        logged_in_user = self.scope['user']
        canvas_pk = self.scope['url_route']['kwargs']['pk']
        
        logged_in_user = self.scope['user']
        canvas_pk = self.scope['url_route']['kwargs']['pk']
        
        text_data_json = json.loads(text_data)
        function = text_data_json['function']

        if function == 'addComment':
            i = text_data_json['i']
            text = text_data_json['input_text']
            idea_pk = text_data_json['idea_pk']

            data = views.new_comment(text, idea_pk, logged_in_user)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'add_comment',
                    'function': function,
                    'comment': data['comment'],
                    'category': data['category'],
                    'i': i
                }
            )


        if function == 'deleteComment':
            i = text_data_json['i']
            c = text_data_json['c']
            comment_pk = text_data_json['comment_pk']

            category = views.delete_comment(logged_in_user, comment_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'delete_comment',
                    'function': function,
                    'category': category,
                    'i': i,
                    'c': c
                }
            )


        if function == 'resolveComments':
            
            i = text_data_json['i']
            idea_pk = text_data_json['idea_pk']

            category = views.comment_resolve(logged_in_user, idea_pk)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'resolve_comments',
                    'function': function,
                    'i': i,
                    'category': category
                }
            )

    async def add_comment(self, event):
        function = event['function']
        comment = event['comment']
        category = event['category']
        i = event['i']

        await self.send(text_data=json.dumps({
            'function': function,
            'i': i,
            'comment': comment,
            'category': category,
        }))

    async def delete_comment(self, event):
        function = event['function']
        i = event['i']
        c = event['c']
        category = event['category']

        await self.send(text_data=json.dumps({
            'function': function,
            'category': category,
            'i': i,
            'c': c
        }))

    async def resolve_comments(self, event):
        function = event['function']
        i = event['i']
        category = event['category']
        
        await self.send(text_data=json.dumps({
            'function': function,
            'i': i,
            'category': category
        }))







class CollabConsumer(AsyncWebsocketConsumer):
    '''
    Consumer for websockets which are for modification of the User model
    '''
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['pk'] + "_collab"
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
        logged_in_user = self.scope['user']
        canvas_pk = self.scope['url_route']['kwargs']['pk']
        
        text_data_json = json.loads(text_data)
        function = text_data_json['function']



        if function == 'addUser':

            name = text_data_json['name']
            user = views.add_user(logged_in_user, canvas_pk, name)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'add_user',
                    'function': function,
                    'user': user
                }
            )



        if function == 'deleteUser':

            user_pk = text_data_json['user_pk']
            ui = text_data_json['ui']
            victim_is_admin = views.delete_user(logged_in_user, canvas_pk, user_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'delete_user',
                    'function': function,
                    'victim_is_admin': victim_is_admin,
                    'ui': ui
                }
            )



        if function == 'promoteUser':

            user_pk = text_data_json['user_pk']
            admin = views.promote_user(logged_in_user, canvas_pk, user_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'promote_user',
                    'function': function,
                    'admin': admin
                }
            )



        if function == 'demoteUser':

            user_pk = text_data_json['user_pk']
            ai = text_data_json['ai']
            views.demote_user(logged_in_user, canvas_pk, user_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'demote_user',
                    'function': function,
                    'ai': ai
                }
            )







    async def add_user(self, event):
        function = event['function']
        user = event['user']

        await self.send(text_data=json.dumps({
                    'function': function,
                    'user': user
        }))



    async def delete_user(self, event):
        function = event['function']
        victim_is_admin = event['victim_is_admin']
        ui = event['ui']

        await self.send(text_data=json.dumps({
                    'function': function,
                    'victimIsAdmin': victim_is_admin,
                    'ui': ui
        }))



    async def promote_user(self, event):
        function = event['function']
        admin = event['admin']

        await self.send(text_data=json.dumps({
                    'function': function,
                    'admin': admin
        }))



    async def demote_user(self, event):
        function = event['function']
        ai = event['ai']

        await self.send(text_data=json.dumps({
            'function': function,
            'ai': ai
        }))


class TagConsumer(AsyncWebsocketConsumer):
    '''
    Consumer for websockets which are for modification of the Tag model
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
        logged_in_user = self.scope['user']
        canvas_pk = self.scope['url_route']['kwargs']['pk']
        
        text_data_json = json.loads(text_data)
        function = text_data_json['function']
        
        if function == 'addTag':

            label = text_data_json['label']
            data = views.add_tag(canvas_pk, logged_in_user, label)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'add_tag',
                    'function': function,
                    'data': data
                }
            )


        if function == 'removeTag':
            i = text_data_json['i']
            tag_pk = text_data_json['tag_pk']

            views.remove_tag(tag_pk, canvas_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'remove_tag',
                    'function': function,
                    'i': i
                }
            )


    async def add_tag(self, event):
        function = event['function']
        data = event['data']


        await self.send(text_data=json.dumps({
            'function': function,
            'tag': data['tag'],
            'public': data['public'],
            'private': data['private'],
            'allCanvasses': data['allCanvasses']
        }))


    async def remove_tag(self, event):
        function = event['function']
        i = event['i']
        
        await self.send(text_data=json.dumps({
            'function': function,
            'i': i
        }))


