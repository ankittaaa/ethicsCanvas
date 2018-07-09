from asgiref.sync import async_to_sync
from django.core import serializers
from channels.db import database_sync_to_async
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from . import views
import json



class TrialIdeaConsumer(WebsocketConsumer):
    '''
    Synchronous consumer for the trial user - does not need to be asynchronous as it's limited to a single user
    '''
    def connect(self):
        self.accept()

    def receive(self, text_data):
        logged_in_user = self.scope['user']
        canvas_pk = self.scope['url_route']['kwargs']['pk']
        
        text_data_json = json.loads(text_data)

        category = text_data_json['category']
        data = views.new_idea(logged_in_user, canvas_pk, category)
        return_idea = data['return_idea']

        idea_pk = data['pk']
        views.delete_idea(logged_in_user, idea_pk)
        # 'Trial' will occur in the function field of newIdea calls made by a trial user. The idea must immediately be deleted, we only want a JSON 
        # model of an idea and not actual idea addition

        self.send(text_data=json.dumps({
            'idea': return_idea
        }))



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
            idea = views.new_idea(logged_in_user, canvas_pk, category)

            data = {
                'idea': idea,
            }


        elif function == 'modifyIdea':
            '''
            MODIFICATION OF IDEA
            '''
            input_text = text_data_json['input_text']
            idea_pk = text_data_json['idea_pk']
            idea_list_index = text_data_json['idea_list_index']
            

            returned = views.edit_idea(logged_in_user, idea_pk, input_text)

            data = {
                'idea': returned['return_idea'],
                'oldText': returned['old_text'],
                'ideaListIndex': idea_list_index,
            }


        elif function == 'deleteIdea':
            '''
            DELETION OF IDEA
            '''
            idea_pk = text_data_json['idea_pk']
            idea_list_index = text_data_json['idea_list_index']
            category = views.delete_idea(logged_in_user, idea_pk),
            
            data =  {
                'category': category,
                'ideaListIndex': idea_list_index
            }


        elif function == 'typing' or function == 'done_typing':
            '''
            USER BEGINS TYPING
            '''
            idea_list_index = text_data_json['idea_list_index']
            category = text_data_json['category']
            username = text_data_json['username']

            data = {
                'ideaListIndex': idea_list_index,
                'category': category,
                'username': username
            }
            
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'channel_message',
                'function': function,
                'data': data
            }
        )


    async def channel_message(self, event):
        function = event['function']
        data = event['data']

        await self.send(text_data=json.dumps({
            'function': function,
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
        logged_in_user = self.scope['user']
        canvas_pk = self.scope['url_route']['kwargs']['pk']
        
        logged_in_user = self.scope['user']
        canvas_pk = self.scope['url_route']['kwargs']['pk']
        
        text_data_json = json.loads(text_data)
        function = text_data_json['function']

        if function == 'addComment':
            idea_list_index = text_data_json['idea_list_index']
            text = text_data_json['input_text']
            idea_pk = text_data_json['idea_pk']

            data = views.new_comment(text, idea_pk, logged_in_user)

            data = {
                'comment': data['comment'],
                'category': data['category'],
                'ideaListIndex': idea_list_index
            }


        elif function == 'deleteComment':
            idea_list_index = text_data_json['idea_list_index']
            comment_list_index = text_data_json['comment_list_index']
            comment_pk = text_data_json['comment_pk']

            category = views.delete_comment(logged_in_user, comment_pk)

            data = {
                'category': category,
                'ideaListIndex': idea_list_index,
                'commentListIndex': comment_list_index
            }

        elif function == 'resolveIndividualComment':
            idea_list_index = text_data_json['idea_list_index']
            comment_list_index = text_data_json['comment_list_index']
            comment_pk = text_data_json['comment_pk']

            category = views.single_comment_resolve(logged_in_user, comment_pk)

            data = {
                'category': category,
                'ideaListIndex': idea_list_index,
                'commentListIndex': comment_list_index
            }


        elif function == 'resolveAllComments':
            idea_list_index = text_data_json['idea_list_index']
            idea_pk = text_data_json['idea_pk']

            category = views.all_comment_resolve(logged_in_user, idea_pk)

            data = {
                'category': category,
                'ideaListIndex': idea_list_index
            }

            
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'channel_message',
                'function': function,
                'data': data,
            }
        )


    async def channel_message(self, event):
        function = event['function']
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'function': function,
            'data': data
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
        project_pk = self.scope['url_route']['kwargs']['pk']
        
        text_data_json = json.loads(text_data)
        function = text_data_json['function']

        if function == 'togglePublic':
            project_pk = text_data_json['canvas_pk']

            views.toggle_public(project_pk, logged_in_user)
            # this returns no data, so we want to skip the reply altogether, hence why it's confined in the 'else' block


        elif function == 'addUser':

            name = text_data_json['name']
            user = views.add_user(logged_in_user, project_pk, name)

            data = {
                'user': user
            }


        elif function == 'deleteUser':

            user_pk = text_data_json['user_pk']
            ui = text_data_json['ui']
            victim_is_admin = views.delete_user(logged_in_user, project_pk, user_pk)

            data = {
                'victimIsAdmin': victim_is_admin,
                'ui': ui
            }


        elif function == 'promoteUser':

            user_pk = text_data_json['user_pk']
            admin = views.promote_user(logged_in_user, project_pk, user_pk)

            data = {
                'admin': admin
            }

        elif function == 'demoteUser':

            user_pk = text_data_json['user_pk']
            ai = text_data_json['ai']
            views.demote_user(logged_in_user, project_pk, user_pk)

            data = {
                'ai': ai
            }

        elif function == 'newActiveUser':
            user = text_data_json['user']
            data = {
                'user': user
            }

        elif function == 'removeActiveUser':
            user = text_data_json['user']
            data = {
                'user': user
            }

        elif function == 'sendWholeList':
            users = text_data_json['users']
            data = {
                'users': users
            }

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'channel_message',
                'function': function,
                'data': data,
            }
        )



    async def channel_message(self, event):
        function = event['function']
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'function': function,
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
        logged_in_user = self.scope['user']
        project_pk = self.scope['url_route']['kwargs']['pk']

        text_data_json = json.loads(text_data)

        function = text_data_json['function']
        label = text_data_json['label']
        canvas_pk = text_data_json['canvas_pk']
        data = []
            
        if function == 'addTag':
            data = views.add_tag(canvas_pk, logged_in_user, label)
        
        elif function == 'deleteTag':
            data = views.delete_tag(canvas_pk, logged_in_user, label)

        elif function == 'removeTag':
            idea_pk = text_data_json['idea_pk']
            data = views.remove_tag(canvas_pk, idea_pk, logged_in_user, label)            
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'channel_message',
                'function': function,
                'data': data,
            }
        )


    async def channel_message(self, event):
        function = event['function']
        data = event['data']

        await self.send(text_data=json.dumps({
            'function': function,
            'data': data
        }))
