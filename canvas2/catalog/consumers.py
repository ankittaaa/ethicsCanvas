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
            data = await database_sync_to_async(views.new_idea)(logged_in_user, canvas_pk, category)
            return_idea = data['return_idea']
            
            idea_pk = data['pk']
            
            # 'Trial' will occur in the function field of newIdea calls made by a trial user. The idea must immediately be deleted, we only want a JSON 
            # model of an idea and not actual idea addition

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'new_idea',
                    'function': 'addIdea',
                    'idea': return_idea
                }
            )

        elif function == 'modifyIdea':
            '''
            MODIFICATION OF IDEA
            '''
            input_text = text_data_json['input_text']
            idea_pk = text_data_json['idea_pk']
            i = text_data_json['i']
            

            data = await database_sync_to_async(views.idea_detail)(logged_in_user, idea_pk, input_text)
            return_idea = data['return_idea']
            old_text = data['old_text']

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'modify_idea',
                    'function': function,
                    'idea': return_idea,
                    'old_text': old_text,
                    'i': i,
                }
            )


        elif function == 'deleteIdea':
            '''
            DELETION OF IDEA
            '''
            idea_pk = text_data_json['idea_pk']
            i = text_data_json['i']

            category = await database_sync_to_async(views.delete_idea)(logged_in_user, idea_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'delete_idea',
                    'function': function,
                    'i': i,
                    'category': category,
                }
            )


        elif function == 'typing' or function == 'done_typing':
            '''
            USER BEGINS TYPING
            '''
            i = text_data_json['i']
            category = text_data_json['category']
            username = text_data_json['username']
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing',
                    'function': function,
                    'i': i, 
                    'username': username,
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
        old_text = event['old_text']
        i = event['i']


        await self.send(text_data=json.dumps({
            'function': function,
            'idea': return_idea,
            'oldText': old_text,
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

    async def typing(self, event):
        i = event['i']
        function = event['function']
        username = event['username']
        category = event['category']

        await self.send(text_data=json.dumps({
            'function': function,
            'i': i, 
            'username': username,
            'category': category,
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

            data = await database_sync_to_async(views.new_comment)(text, idea_pk, logged_in_user)

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


        elif function == 'deleteComment':
            i = text_data_json['i']
            c = text_data_json['c']
            comment_pk = text_data_json['comment_pk']

            category = await database_sync_to_async(views.delete_comment)(logged_in_user, comment_pk)

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

        elif function == 'resolveIndividualComment':
            i = text_data_json['i']
            c = text_data_json['c']
            comment_pk = text_data_json['comment_pk']

            category = await database_sync_to_async(views.single_comment_resolve)(logged_in_user, comment_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'resolve_individual_comment',
                    'function': function,
                    'category': category,
                    'i': i,
                    'c': c
                }
            )


        elif function == 'resolveAllComments':
            
            i = text_data_json['i']
            idea_pk = text_data_json['idea_pk']

            category = await database_sync_to_async(views.all_comment_resolve)(logged_in_user, idea_pk)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'resolve_all_comments',
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

    async def resolve_individual_comment(self, event):
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

    async def resolve_all_comments(self, event):
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
        project_pk = self.scope['url_route']['kwargs']['pk']
        
        text_data_json = json.loads(text_data)
        function = text_data_json['function']


        if function == 'addUser':

            name = text_data_json['name']
            user = await database_sync_to_async(views.add_user)(logged_in_user, project_pk, name)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'add_user',
                    'function': function,
                    'user': user
                }
            )

        elif function == 'deleteUser':

            user_pk = text_data_json['user_pk']
            ui = text_data_json['ui']
            victim_is_admin = await database_sync_to_async(views.delete_user)(logged_in_user, project_pk, user_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'delete_user',
                    'function': function,
                    'victim_is_admin': victim_is_admin,
                    'ui': ui
                }
            )

        elif function == 'promoteUser':

            user_pk = text_data_json['user_pk']
            admin = await database_sync_to_async(views.promote_user)(logged_in_user, project_pk, user_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'promote_user',
                    'function': function,
                    'admin': admin
                }
            )

        elif function == 'demoteUser':

            user_pk = text_data_json['user_pk']
            ai = text_data_json['ai']
            await database_sync_to_async(views.demote_user)(logged_in_user, project_pk, user_pk)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'demote_user',
                    'function': function,
                    'ai': ai
                }
            )

        elif function == 'newActiveUser':
            user = text_data_json['user']

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'new_active_user',
                    'function': function,
                    'user': user,
                }
            )

        elif function == 'removeActiveUser':
            user = text_data_json['user']

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'remove_active_user',
                    'function': function,
                    'user': user,
                }
            )

        elif function == 'sendWholeList':
            users = text_data_json['users']

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_whole_list',
                    'function': function,
                    'users': users,
                }
            )

        elif function == 'togglePublic':
            project_pk = text_data_json['canvas_pk']

            await database_sync_to_async(views.toggle_public)(project_pk, logged_in_user)


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


    async def new_active_user(self, event):
        function = event['function']
        user = event['user']

        await self.send(text_data=json.dumps({
            'function': function,
            'user': user,
        }))


    async def remove_active_user(self, event):
        function = event['function']
        user = event['user']

        await self.send(text_data=json.dumps({
            'function': function,
            'user': user,
        }))


    async def send_whole_list(self, event):
        function = event['function']
        users = event['users']

        await self.send(text_data=json.dumps({
            'function': function,
            'users': users,
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
            data = await database_sync_to_async(views.add_tag)(canvas_pk, logged_in_user, label)
        
        elif function == 'deleteTag':
            data = await database_sync_to_async(views.delete_tag)(canvas_pk, logged_in_user, label)

        elif function == 'removeTag':
            idea_pk = text_data_json['idea_pk']
            data = await database_sync_to_async(views.remove_tag)(canvas_pk, idea_pk, logged_in_user, label)            
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'tag_return',
                'function': function,
                'data': data,
            }
        )


    async def tag_return(self, event):
        function = event['function']
        data = event['data']

        await self.send(text_data=json.dumps({
            'function': function,
            'data': data
        }))
