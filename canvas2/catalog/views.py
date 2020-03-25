from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse, reverse_lazy

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.backends.base import SessionBase

from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize
from django.core import serializers

from django.utils.html import strip_tags
from django.db.models import Q
from channels.db import database_sync_to_async
from django.db.models.query import EmptyQuerySet

from .models import Canvas, CanvasTag, Idea, IdeaComment, Project
from .forms import SignUpForm, IdeaForm, CommentForm, AddUserForm
from . import consumers

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer, AsyncConsumer

import django.utils.timezone

# TODO: change serialization methods from needing to pass a singleton list to accepting a single model instance (each marked below)

'''
TODO: nullable owner field, blank admins & users - this is for a 'blank' project that 'blank' canvasses use, which the trial user
uses. The selected trial canvas is currently downloaded as any other canvas, and a new idea is created like other ones, but the idea
is not added to the canvas model in the database. It is just so that a blank idea can be sent back to the trial user and appended
to the list of ideas in the front-end. This is why View functions, when testing for user permissions, also check for project.title == blank-project

This approach was written as a 'quick-fix', a better solution should be investigated.
'''


##################################################################################################################################
#                                                           CANVAS VIEWS                                                         #
##################################################################################################################################



def new_canvas(request, canvas_type):
    creator = request.user

    if creator.is_authenticated:

        split_url = request.META.get('HTTP_REFERER').split('/')
        project_pk = split_url[len(split_url) - 2]
        project = Project.objects.get(pk=project_pk)

        # canvas_type integer: 0 for Ethics, 1 for Business, 2 for Privacy
        canvas = Canvas(canvas_type=canvas_type, project=project)
        canvas.save()
        canvas.title =  f'New Canvas {canvas.pk} (Ethics)' if canvas_type == 0 else f'New Canvas {canvas.pk} (Business)' if canvas_type == 1 else f'New Canvas {canvas.pk} (Privacy)'
        canvas.save()

        return redirect(canvas.get_absolute_url()) # bring user to the canvas page for the newly created canvas

    else:
        # NOTE: code below relates to blank project
        # check that a blank canvas exists - this will be used to render a blank canvas for the anonymous user to interact with

        if Project.objects.filter(title='blank-project').exists() == False:
            project = Project(title='blank-project')
            project.save()

        else:
            project = Project.objects.get(title='blank-project', is_public=False)

            if canvas_type == 0:

                if Canvas.objects.filter(title='blank-ethics').exists():
                    return redirect(Canvas.objects.get(title='blank-ethics').get_absolute_url())
                else :
                # if there is no blank canvas, create one. set public to false so that it remains blank
                    canvas = Canvas(title='blank-ethics', canvas_type=canvas_type, project=project)
                    canvas.save()
                    return redirect(canvas.get_absolute_url()) # bring user to the canvas page for the newly created canvas

            elif canvas_type == 1:
                if Canvas.objects.filter(title='blank-business').exists():
                    return redirect(Canvas.objects.get(title='blank-business').get_absolute_url())
                else :
                # if there is no blank canvas, create one. set public to false so that it remains blank
                    canvas = Canvas(title='blank-business', canvas_type=canvas_type, project=project)
                    canvas.save()
                    return redirect(canvas.get_absolute_url()) # bring user to the canvas page for the newly created canvas

            elif canvas_type == 2:
                if Canvas.objects.filter(title='blank-privacy').exists():
                    return redirect(Canvas.objects.get(title='blank-business').get_absolute_url())
                else :
                # if there is no blank canvas, create one. set public to false so that it remains blank
                    canvas = Canvas(title='blank-privacy', canvas_type=canvas_type, project=project)
                    canvas.save()
                    return redirect(canvas.get_absolute_url()) # bring user to the canvas page for the newly created canvas


def new_project(request):
    creator = request.user

    project = Project(owner=creator)
    project.save()

    project.title = f'Project {project.pk}'
    project.admins.add(creator)
    project.users.add(creator)
    project.save()

    return redirect(project.get_absolute_url())



def delete_canvas(request, pk):
    '''
    Function for deleting a canvas
    '''
    user = request.user
    canvas = Canvas.objects.get(pk = pk)
    tags = canvas.tags.all()

    for tag in tags:
        tag.canvas_set.remove(canvas)
        tag.save()

    if (not admin_permission(user, canvas.project)):
        return HttpResponse('Forbidden', status=403)

    canvas.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_project(request, pk):
    '''
    Function for deleting a canvas
    '''
    user = request.user
    project = Project.objects.get(pk = pk)

    if (project.owner != user):
        return HttpResponse('Forbidden', status=403)

    project.delete()
    return redirect(request.META.get('HTTP_REFERER'))

##################################################################################################################################
#                                                   CANVAS CLASS-BASED VIEWS                                                     #
##################################################################################################################################


class ProjectListView(LoginRequiredMixin, generic.ListView):
    model = Project

    def get_context_data(self, **kwargs):
        '''
        This function's purpose is to separate the public from the private canvases
        '''
        logged_in_user = self.request.user
        context = super().get_context_data(**kwargs)

        filter_kwargs = {'is_public': True}
        user_filter_kwargs = {'users': logged_in_user}
        admin_filter_kwargs = {'admins': logged_in_user}

        # public projects are those where public is true
        public = Project.objects.filter(**filter_kwargs)
        # private projects where the user is either the owner or a collaborator on the canvas
        private = Project.objects.exclude(**filter_kwargs)

        my_private = (
            private.filter(**admin_filter_kwargs) | private.filter(**user_filter_kwargs)
        ).distinct()

        all_projects = (
            Project.objects.filter(**filter_kwargs) | private.filter(**admin_filter_kwargs) | private.filter(**user_filter_kwargs)
        ).distinct()

        context['public_projects'] = public
        context['private_projects'] = my_private
        context['all_projects'] = all_projects

        return context

class ProjectDetailView(generic.DetailView):
    model = Project

    def get(self, request, pk):

        logged_in_user = self.request.user
        project = Project.objects.get(pk=pk)

        if (not user_permission(logged_in_user, project)):
            return {
                'error': 401,
                'response': 'unauthorized'
            }

        if request.is_ajax():
            json_users = '""'
            json_admins = '""'

            users = project.users.all()
            admins = project.admins.all()
            current = [logged_in_user]

            json_admins = serialize(
                'json',
                admins,
                cls = UserModelEncoder
            )

            json_users = serialize(
                'json',
                users,
                cls = UserModelEncoder
            )

            json_self=serialize(
                'json',
                current,
                cls=UserModelEncoder
            )
            # single user - remove enclosing square brackets
            json_self = json_self[1:-1]

            data = {
                'admins': json_admins,
                'users': json_users,
                'loggedInUser': json_self,

            }
            return JsonResponse(data, safe = False)


        else:
            canvas_list = Canvas.objects.filter(project=project)

            return render(
                request,
                'catalog/project_detail.html',
                {
                    'user': logged_in_user,
                    'canvases': canvas_list
                }
            )

class CanvasDetailView(generic.DetailView):
    model = Canvas

    def get(self, request, pk):
        '''
        function for post requests, sent by a canvas on loading
        purpose is to return the canvas information as a JSON
        '''
        logged_in_user = request.user

        canvas_pk = pk
        canvas = Canvas.objects.get(pk = canvas_pk)
        project = canvas.project

        # no user permission and the canvas isn't the blank one
        if (not user_permission(logged_in_user, project) and 'blank-' not in canvas.title):
            return {
                'error': 401,
                'response': 'unauthorized'
            }

        if request.is_ajax():
            # initialise every json_object as the empty string
            null_tag = CanvasTag(label=None)
            json_comments = '""'
            json_ideas = '""'
            json_tags = '""'
            json_self = '""'
            json_users = '""'
            json_admins = '""'

            if (logged_in_user.is_authenticated):
                current = [logged_in_user]

            else:
                current = project.users.none()
                comments = "''"


            ideas = Idea.objects.filter(canvas=canvas)
            # every tag attached to an idea in this current canvas
            tags = CanvasTag.objects.filter(idea_set__in=ideas).distinct()
            # every tag in the entire project
            all_tags = CanvasTag.objects.filter(canvas_set__in=Canvas.objects.filter(project=project)).distinct()

            # initialise these as empty lists - they will become lists of lists as each tag may have several tagged ideas and canvases
            tagged_ideas_json = []
            tagged_canvases_json = []

            for t in tags:
                '''
                Only need the tagged ideas and canvasses for the tags that will actually be rendered ie the tags in the current canvas
                '''
                tagged_ideas_json.append(
                    serialize(
                        'json',
                        t.idea_set.all(),
                        cls=IdeaEncoder
                    )
                )

                tagged_canvases_json.append(
                    serialize(
                        'json',
                        t.canvas_set.all(),
                        cls=CanvasEncoder
                    )
                )

            comments = IdeaComment.objects.filter(idea__in=ideas)
            # need the users list for the comment authors, when the comment is parsed the PK of the user is what's used for the user FK, not the user object itself
            users = project.users.all()
            # also need the admins for enabling or disabling certain buttons
            admins = project.admins.all()

            if tags:
                json_tags = serialize(
                    'json',
                    tags,
                    cls = CanvasTagEncoder
                )

            else:
                # a null tag is used for conditionally rendering the tag Vue element

                # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
                json_tags = serialize(
                    'json',
                    [null_tag],
                    cls = CanvasTagEncoder
                )
                # singular tag, replace enclosing square brackets with curly brackets
                json_tags = json_tags[1:-1]

            if all_tags:
                json_all_tags = serialize(
                    'json',
                    all_tags,
                    cls = CanvasTagEncoder
                )

            else:
                # a null tag is used for conditionally rendering the tag Vue element
                tag = CanvasTag(label=None)
                # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
                json_all_tags = serialize(
                    'json',
                    [null_tag],
                    cls = CanvasTagEncoder
                )
                # singular tag, remove enclosing square brackets
                json_all_tags = json_all_tags[1:-1]

            if comments:
                json_comments = serialize(
                    'json',
                    comments,
                    cls = IdeaCommentEncoder
                )

            # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
            # NB: current assigned above as either empty string if Anon. user or [logged_in_user] if is_authenticated
            json_self=serialize(
                'json',
                current,
                cls=UserModelEncoder
            )

            if logged_in_user.is_authenticated:
                # singular user, remove enclosing square brackets
                json_self = json_self[1:-1]


            # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
            json_canvas=serialize(
                'json',
                [canvas],
                cls=CanvasEncoder
            )

            # singular canvas, remove enclosing square brackets
            json_canvas = json_canvas[1:-1]


            json_users=serialize(
                'json',
                users,
                cls=UserModelEncoder
            )

            json_admins=serialize(
                'json',
                admins,
                cls=UserModelEncoder
            )

            # only serialise ideas if they exist
            if ideas:
                json_ideas = serialize(
                    'json',
                    ideas,
                    cls = IdeaEncoder
                )


            data = {
                'ideas': json_ideas,
                'comments': json_comments,
                'tags': json_tags,
                'allTags': json_all_tags,
                'loggedInUser': json_self,
                'allTaggedIdeas': tagged_ideas_json,
                'taggedCanvases': tagged_canvases_json,
                'thisCanvas': json_canvas,
                'projectPK': project.pk,
                'users': json_users,
                'admins': json_admins,
            }

            return JsonResponse(data, safe = False)
        else:
            '''
            This 'else' is for the initial page load. document.onload currently triggers the AJAX GET request which gets all
            the relevant canvas information as JSON objects
            '''
            return render(
                request,
                'catalog/canvas_detail.html',
                {
                    'user': logged_in_user,
                    'project': project,
                },
            )


##################################################################################################################################
#                                                         IDEA VIEWS                                                             #
##################################################################################################################################

def new_trial_idea(request):
    '''
    NOTE: BLANK CANVAS, TRIAL USER IDEA ADDITION
    '''
    if request.method == 'POST':
        print("..")
        canvas_pk = request.POST['canvas_pk']
        try:
            canvas = Canvas.objects.get(pk=canvas_pk)
        except Canvas.DoesNotExist:
            return HttpResponse('Canvas does not exist', status=404)

        logged_in_user = request.user

        project = canvas.project
        # can't add ideas if the canvas is unavailable or if the blank canvas is being edited to by an authenticated user
        if (not user_permission(logged_in_user, project) and ('blank-' not in canvas.title and logged_in_user.is_authenticated)):
            return HttpResponse('Unauthorized', status=401)

        category = request.POST['idea_category']

        idea = Idea(
            canvas = canvas,
            category = category,
            text = '',
            title = f'Canvas {canvas_pk} TRIAL IDEA'
        )
        idea.save()

        # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
        return_idea = serialize(
            'json',
            [idea],
            cls=IdeaEncoder
        )
        idea.delete()

        # singular idea, remove enclosing square brackets
        return_idea = return_idea[1:-1]
        data = {
            'idea': return_idea,
        }

        return JsonResponse(data)

def delete_trial_idea(idea_pk):
    '''
    NOTE: BLANK CANVAS, TRIAL USER IDEA DELETION - IMM
    '''
    Idea.objects.get(pk=idea_pk).delete()



def new_idea(request):
    '''
    Creation of a new idea. This gets the id for the canvas in which it is created from the calling URL
    '''
    if request.method == 'POST':
        canvas_pk = request.POST['canvas_pk']
        category = request.POST['idea_category']
        logged_in_user = request.user


        try:
            canvas = Canvas.objects.get(pk = canvas_pk)
            project = canvas.project
        except:
            Canvas.DoesNotExist
            return HttpResponse('Canvas does not exist', status=404)

            Project.DoesNotExist
            return HttpResponse('Project does not exist', status=404)

        # can't add ideas if the canvas is unavailable or if the blank canvas is being edited to by an authenticated user
        if (not user_permission(logged_in_user, project) and ('blank-' not in canvas.title and logged_in_user.is_authenticated)):
            return HttpResponse('Unauthorized', status=401)



        idea = Idea(
            canvas = canvas,
            category = category,
            text = ''
        )
        idea.save()
        # This is so I can click on it in the django admin - should probably delete later
        idea.title = f'Canvas {canvas_pk} Idea {idea.pk}'
        idea.save()


        # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
        return_idea = serialize(
            'json',
            [idea],
            cls=IdeaEncoder
        )
        # singular idea, remove enclosing square brackets
        return_idea = return_idea[1:-1]

        channel_layer = get_channel_layer()

        room_name = canvas_pk + "_idea"
        room_group_name = 'canvas_%s' %room_name

        data = {
            'function': request.POST['function'],
            'idea': return_idea,
        }

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)



def delete_idea(request):
    '''
    Deletion of an idea
    '''
    if request.method == 'POST':
        try:
            logged_in_user = request.user
            idea_pk = request.POST['idea_pk']

            idea = Idea.objects.get(pk=idea_pk)
            canvas = idea.canvas
            project = canvas.project

        except:
            Idea.DoesNotExist
            return HttpResponse('Idea does not exist', status=404)

            Canvas.DoesNotExist
            return HttpResponse('Canvas does not exist', status=404)

            Project.DoesNotExist
            return HttpResponse('Project does not exist', status=404)

        # can't remove ideas if the canvas is unavailable or if the blank canvas is being edited by an authenticated user
        if (not user_permission(logged_in_user, project) and ('blank-' not in canvas.title and logged_in_user.is_authenticated)):
            return HttpResponse('Unauthorized', status=401)

        category = idea.category

        # get every tag associated with the idea
        tags = idea.tags.all()
        removed_tags = []

        json_tagged_canvases = []
        json_tagged_ideas = []
        json_tags = []

        # iterate through the tags, removing the idea from each
        for tag in tags:
            tag.idea_set.remove(idea)
            tag.save()

            # check if any ideas remain
            updated_ideas = tag.idea_set.filter(canvas=canvas).distinct()

            # if no idaes remain, remove the canvas from the tag's canvas set as well
            if not updated_ideas:
                tag.canvas_set.remove(canvas)
                tag.save()
                canvas.save()

            removed_tags.append(tag)


        return_tag_data = []

        for tag in removed_tags:

            json_tagged_canvases=(
                serialize(
                    'json',
                    tag.canvas_set.all(),
                    cls=CanvasEncoder
                )
            )

            json_tagged_ideas=(
                serialize(
                    'json',
                    tag.idea_set.all(),
                    cls=IdeaEncoder
                )
            )

            json_tags=(
                serialize(
                    'json',
                    [tag],
                    cls = CanvasTagEncoder
                )
            )
            json_tags = json_tags[1:-1]

            tag_data = {
                'taggedCanvases': json_tagged_canvases,
                'taggedIdeas': json_tagged_ideas,
                'tags': json_tags,
            }

            return_tag_data.append(tag_data)

        # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
        return_idea = serialize(
            'json',
            [idea],
            cls=IdeaEncoder
        )
        # singular idea, remove enclosing square brackets
        return_idea = return_idea[1:-1]

        idea.delete()


        data = {
            'function': request.POST['function'],
            'returnTagData': return_tag_data,
            'idea': return_idea,
            'ideaCategory': category,
            'ideaListIndex': request.POST['idea_list_index']
        }

        channel_layer = get_channel_layer()

        room_name = f"{canvas.pk}_idea"
        room_group_name = 'canvas_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)




def edit_idea(request):
    '''
    Update of an idea
    '''
    if request.method == 'POST':
        try:
            logged_in_user = request.user
            idea_pk = request.POST['idea_pk']
            input_text = request.POST['input_text']

            idea = Idea.objects.get(pk = idea_pk)
            canvas = idea.canvas
            project = canvas.project

        except:
            Idea.DoesNotExist
            return HttpResponse('Idea does not exist', status=404)

            Canvas.DoesNotExist
            return HttpResponse('Canvas does not exist', status=404)

            Project.DoesNotExist
            return HttpResponse('Project does not exist', status=404)


        current_tags_in_idea = idea.tags.all()

        old_text = idea.text

        if (not user_permission(logged_in_user, project) or (project.title == 'blank-project')):
            return HttpResponse('Unauthorized', status=401)

        input_text = strip_tags(input_text)

        updated_tags_in_idea = []

        new_tags = []
        new_tags_canvas_set = []
        new_tags_idea_set = []

        removed_tags = []
        removed_tags_canvas_set = []
        removed_tags_idea_set = []

        # check if any of the tags are implicitly removed or inserted by their labels no longer occurring in the idea or newly occurring in the idea respectively
        for temp_canvas in project.canvas_set.all():
            for tag in temp_canvas.tags.all():

                # if the tag is in the input_text, add it. RHS of and operation is to keep the list elements unique
                if tag.label in input_text and tag not in updated_tags_in_idea:
                    updated_tags_in_idea.append(tag)

                # if it was in the old text and no longer occurs, remove it
                elif tag.label in old_text and tag.label not in input_text:
                    removed_tags.append(tag)


        # update the tags field in canvas by setting them - implicitly remove the removed tags
        canvas.tags.set(updated_tags_in_idea)
        canvas.save()

        # the same for idea's tags field
        idea.tags.set(updated_tags_in_idea)
        idea.text = input_text
        idea.save()

        new_return_tag_data = []
        removed_return_tag_data = []

        # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
        return_idea = serialize(
            'json',
            [idea],
            cls=IdeaEncoder
        )
        return_idea = return_idea[1:-1]



        for tag in updated_tags_in_idea:

            new_tags=(
                serialize(
                    'json',
                    [tag],
                    cls = CanvasTagEncoder
                )
            )
            new_tags = new_tags[1:-1]

            new_tags_canvas_set=(
                serialize(
                    'json',
                    tag.canvas_set.all(),
                    cls=CanvasEncoder
                )
            )

            new_tags_idea_set=(
                serialize(
                    'json',
                    tag.idea_set.all(),
                    cls=IdeaEncoder
                )
            )


            tag_data = {
                'newTag': new_tags,
                'newTaggedCanvases': new_tags_canvas_set,
                'newTaggedIdeas': new_tags_idea_set,
            }

            new_return_tag_data.append(tag_data)

        for tag in removed_tags:

            # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
            removed_tags=(
                serialize(
                    'json',
                    [tag],
                    cls = CanvasTagEncoder
                )
            )
            removed_tags = removed_tags[1:-1]

            removed_tags_canvas_set=(
                serialize(
                    'json',
                    tag.canvas_set.all(),
                    cls=CanvasEncoder
                )
            )

            removed_tags_idea_set=(
                serialize(
                    'json',
                    tag.idea_set.all(),
                    cls=IdeaEncoder
                )
            )

            tag_data = {
                'removedTag': removed_tags,
                'removedTaggedCanvases': removed_tags_canvas_set,
                'removedTaggedIdeas': removed_tags_idea_set,
            }

            removed_return_tag_data.append(tag_data)

        data = {
            'function': request.POST['function'],
            'removedReturnTagData': removed_return_tag_data,
            'newReturnTagData': new_return_tag_data,
            'idea': return_idea,
            'oldText': old_text,
            'ideaCategory': idea.category,
            'ideaListIndex': request.POST['idea_list_index'],
        }

        channel_layer = get_channel_layer()

        room_name = f"{canvas.pk}_idea"
        room_group_name = 'canvas_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)




##################################################################################################################################
#                                                       COMMENT VIEWS                                                            #
##################################################################################################################################


def new_comment(request):
    if request.method == 'POST':
        logged_in_user = request.user
        idea_pk = request.POST['idea_pk']
        input_text = request.POST['input_text']


        try:
            idea = Idea.objects.get(pk=idea_pk)
            canvas = idea.canvas
            project = canvas.project

        except:
            Idea.DoesNotExist
            return HttpResponse('Idea does not exist.', status=404)

            Canvas.DoesNotExist
            return HttpResponse('Canvas does not exist.', status=404)

            Project.DoesNotExist
            return HttpResponse('Project does not exist.', status=404)


        if (not user_permission(logged_in_user, project) or (project.title == 'blank-project')):
            return HttpResponse('Unauthorized', status=401)


        text = input_text
        text = strip_tags(text)

        comment = IdeaComment(
            user = logged_in_user,
            text = text,
            idea = idea
        )
        comment.save()

        # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
        json_comment = serialize(
            'json',
            [comment],
            cls = IdeaCommentEncoder
        )

        # singular comment, remove enclosing square brackets
        json_comment = json_comment[1:-1]

        data = {
            'function': request.POST['function'],
            'comment': json_comment,
            'ideaCategory': idea.category,
            'ideaListIndex': request.POST['idea_list_index']
        }

        channel_layer = get_channel_layer()

        room_name = f"{canvas.pk}_comment"
        room_group_name = 'canvas_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)


def delete_comment(request):
    '''
    Deletion of a comment
    '''
    if request.method == 'POST':
        logged_in_user = request.user
        comment_pk = request.POST['comment_pk']

        try:
            comment = IdeaComment.objects.get(pk=comment_pk)
            canvas = comment.idea.canvas
            project = canvas.project

        except:
            IdeaComment.DoesNotExist
            return HttpResponse('Comment does not exist.', status=404)

            Canvas.DoesNotExist
            return HttpResponse('Canvas does not exist.', status=404)

            Project.DoesNotExist
            return HttpResponse('Project does not exist.', status=404)


        if (not admin_permission(logged_in_user, project) or (project.title == 'blank-project')):
            return HttpResponse('Forbidden.', status=403)


        category = comment.idea.category
        comment.delete()


        data = {
            'function': request.POST['function'],
            'ideaCategory': category,
            'ideaListIndex': request.POST['idea_list_index'],
            'commentListIndex': request.POST['comment_list_index'],
        }

        channel_layer = get_channel_layer()

        room_name = f"{canvas.pk}_comment"
        room_group_name = 'canvas_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)



def single_comment_resolve(request):
    '''
    Resolution of a single comment
    '''
    if request.method == 'POST':
        logged_in_user = request.user
        comment_pk = request.POST['comment_pk']

        try:
            comment = IdeaComment.objects.get(pk=comment_pk)
            canvas = comment.idea.canvas
            project = canvas.project

        except:
            IdeaComment.DoesNotExist
            return HttpResponse('Comment does not exist.', status=404)

            Canvas.DoesNotExist
            return HttpResponse('Canvas does not exist.', status=404)

            Project.DoesNotExist
            return HttpResponse('Project does not exist.', status=404)


        if (not admin_permission(logged_in_user, project) or (project.title == 'blank-project')):
            return HttpResponse('Forbidden.', status=403)

        category = comment.idea.category
        comment.resolved = True
        comment.save()

        data = {
            'function': request.POST['function'],
            'ideaCategory': category,
            'ideaListIndex': request.POST['idea_list_index'],
            'commentListIndex': request.POST['comment_list_index'],
        }

        channel_layer = get_channel_layer()

        room_name = f"{canvas.pk}_comment"
        room_group_name = 'canvas_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)



def all_comment_resolve(request):
    '''
    Resolution of comments - mark all as resolved
    '''
    if request.method == 'POST':
        logged_in_user = request.user
        idea_pk = request.POST['idea_pk']

        try:
            idea = Idea.objects.get(pk = idea_pk)
            canvas = idea.canvas
            project = canvas.project
        except:
            Idea.DoesNotExist
            return HttpResponse('Idea does not exist.', status=404)

            Canvas.DoesNotExist
            return HttpResponse('Canvas does not exist.', status=404)

            Project.DoesNotExist
            return HttpResponse('Project does not exist.', status=404)


        if (not admin_permission(logged_in_user, project) or (project.title == 'blank-project')):
            return HttpResponse('Forbidden.', status=403)

        IdeaComment.objects.all().filter(idea = idea).update(resolved=True)


        data = {
            'function': request.POST['function'],
            'ideaCategory': idea.category,
            'ideaListIndex': request.POST['idea_list_index'],
        }

        channel_layer = get_channel_layer()

        room_name = f"{canvas.pk}_comment"
        room_group_name = 'canvas_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)


##################################################################################################################################
#                                           COLLABORATOR AND LANDING PAGE VIEWS                                                  #
##################################################################################################################################


def index(request):
    return render(request, 'index.html')



def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            newUser = User.objects.create_user(
                username = username,
                email = email,
                password = password
            )

            return HttpResponseRedirect(reverse('index'))

    else:
        form = SignUpForm(initial = {
            'name': '',
            'email': '',
            'password': '',
            'password2': '',
        })


    return render(
        request,
        'catalog/register.html',
        {'form': form}
    )

def add_user(request):
    '''
    Function for addition of user to project
    '''
    if request.method == 'POST':
        project_pk = request.POST['project_pk']

        try:
            project = Project.objects.get(pk=project_pk)
        except:
            Project.DoesNotExist
            return HttpResponse('Project does not exist.', status=404)

        name = request.POST['name']

        logged_in_user = request.user
        # check is admin
        if (not admin_permission(logged_in_user, project)):
            return HttpResponse('Forbidden.', status=403)


        else:
            try:
                user = User.objects.get(username=name)
            except:
                User.DoesNotExist
                return HttpResponse('User does not exist.', status=404)

            if user in project.users.all() or user in project.admins.all():
                reply = ''

                if user is logged_in_user:
                    reply = 'Error: you\'re already a collaborator, you can\'t add yourself!'

                else:
                    reply = 'Error: ' + name + ' is already a collaborator!'

                return HttpResponse(reply, status=500)


            project.users.add(user)

            # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
            json_user = serialize(
                'json',
                [user],
                cls = UserModelEncoder
            )
            # singular user - remove enclosing square brackets
            json_user = json_user[1:-1]

            data = {
                'function': request.POST['function'],
                'user': json_user,
            }

            channel_layer = get_channel_layer()

            room_name = project_pk + "_collab"
            room_group_name = 'project_%s' %room_name

            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'channel_message',
                    'data': data
                }
            )

            return HttpResponse(status=200)

def delete_user(request):
    '''
    Function for deleting a user from the project.
    '''
    if request.method == 'POST':
        project_pk = request.POST['project_pk']

        try:
            project = Project.objects.get(pk=project_pk)
        except:
            Project.DoesNotExist
            return HttpResponse('Project does not exist.', status=404)

        logged_in_user = request.user
        # check is admin
        if (not admin_permission(logged_in_user, project)):
            return HttpResponse('Forbidden', status=403)


        try:
            user = User.objects.get(pk=request.POST['user_pk'])
        except:
            User.DoesNotExist
            return HttpResponse('User does not exist.', status=404)

        if user not in project.users.all():
            reply = 'Error: ' + name + ' is not a collaborator'
            return HttpResponse(reply, status=500)

        admins = project.admins.all()

        # if there is one admin who is the logged-in user, do not allow them to
        # delete themselves. It's implied that if there's one admin, the logged_in
        # user is that admin, as earlier it is checked that the logged_in user
        # is in the project admin set
        if (len(admins) == 1 and user in admins):
            reply = 'Error: You are the only admin, you may not delete yourself!'
            return HttpResponse(reply, status=500)

        victim_is_admin = "false"
        # if the user is also an admin, remove them from that field also
        if user in admins:
            victim_is_admin = "true"
            project.admins.remove(user)

        project.users.remove(user)

        data = {
            'function': request.POST['function'],
            'userListIndex': request.POST['user_list_index'],
            'victimIsAdmin': victim_is_admin,
        }

        channel_layer = get_channel_layer()

        room_name = project_pk + "_collab"
        room_group_name = 'project_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)


def promote_user(request):
    '''
    Function for promoting a user to admin status
    '''
    if request.method == 'POST':
        project_pk = request.POST['project_pk']
        try:
            project = Project.objects.get(pk=project_pk)
        except:
            Project.DoesNotExist
            return HttpResponse('Project does not exist', status=404)

        logged_in_user = request.user
        # check is admin
        if (not admin_permission(logged_in_user, project)):
                return HttpResponse('Forbidden', status=403)

        try:
            user = User.objects.get(pk=request.POST['user_pk'])
        except:
            User.DoesNotExist
            return HttpResponse('User does not exist', status=404)


        name_str = user.username
        admins = project.admins.all()

        # check presence in admin set
        if user in admins:
            # additionally check the user isn't trying to promote themselves
            if user is logged_in_user:
                name_str = 'you are'
            else:
                name_str = name_str + ' is '
            reply = 'Error: ' + name_str + ' already an admin!'

            return HttpResponse(reply, status=500)

        project.admins.add(user)

        # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
        json_user = serialize(
            'json',
            [user],
            cls = UserModelEncoder
        )
        # singular user - remove enclosing square brackets
        json_user = json_user[1:-1]

        data = {
            'function': request.POST['function'],
            'admin': json_user,
        }

        channel_layer = get_channel_layer()

        room_name = project_pk + "_collab"
        room_group_name = 'project_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)


def demote_user(request):
    '''
    Function to delete a user from the admin field - this is for demotion only.
    For complete deletion, call delete user
    '''
    if request.method == 'POST':
        project_pk = request.POST['project_pk']
        try:
            project = Project.objects.get(pk=project_pk)
        except:
            Project.DoesNotExist
            return HttpResponse('Project does not exist', status=404)

        logged_in_user = request.user
        # check is admin
        if (not admin_permission(logged_in_user, project)):
                return HttpResponse('Forbidden', status=403)

        try:
            user = User.objects.get(pk=request.POST['user_pk'])
        except:
            User.DoesNotExist
            return HttpResponse('User does not exist', status=404)

        admins = project.admins.all()
        # Can't delete a non-existent admin
        if user not in admins:
            reply = 'Error: ' + name + ' is not an admin'
            return HttpResponse(reply, status=500)

        # if there is one admin who is the logged-in user, do not allow them to
        # delete themselves
        if len(admins) == 1:
            reply = 'Error: You are the only admin, you may not demote yourself!'
            return HttpResponse(reply, status=500)

        project.admins.remove(user)

        data = {
            'function': request.POST['function'],
            'adminListIndex': request.POST['admin_list_index']
        }

        channel_layer = get_channel_layer()

        room_name = project_pk + "_collab"
        room_group_name = 'project_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)


def toggle_public(request):
    if request.method == 'POST':
        project_pk = request.POST['project_pk']

        try:
            project = Project.objects.get(pk=project_pk)
        except:
            Project.DoesNotExist
            return HttpResponse('Project does not exist', status=404)

        logged_in_user = request.user
        # check is admin
        if (not admin_permission(logged_in_user, project)):
                return HttpResponse('Forbidden', status=403)

        project.is_public = not(project.is_public)
        project.save()

        data = {
            'function': request.POST['function'],
        }

        channel_layer = get_channel_layer()

        room_name = project_pk + "_collab"
        room_group_name = 'project_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)




##################################################################################################################################
#                                                           TAG VIEWS                                                            #
##################################################################################################################################

def add_tag(request):
    '''
    ADDITION OF NEW TAG
    '''
    if request.method == 'POST':
        try:
            canvas = Canvas.objects.get(pk=request.POST['canvas_pk'])
            print(canvas)
            project = canvas.project

        except:
            Canvas.DoesNotExist
            return HttpResponse('Canvas does not exist.', status=404)

            Project.DoesNotExist
            return HttpResponse('Project does not exist.', status=404)

        logged_in_user = request.user
        label = request.POST['label']

        if (not user_permission(logged_in_user, project) or (project.title == 'blank-project')):
            return HttpResponse('Unauthorized', status=401)

        # check existence of tag within project - avoid duplicating tags
        if CanvasTag.objects.filter(label=label, canvas_set__project=project).exists():
            tag = CanvasTag.objects.get(label=label)

            tag_canvas_set = tag.canvas_set.all()

            if canvas not in tag_canvas_set:
                tag.canvas_set.add(canvas)


        else:
            # only create tag if it doesn't exist anywhere visible to the user
            tag = CanvasTag(label=label)
            tag.save()
            tag.canvas_set.add(canvas)

        tag.save()
        canvas.save()

        # check every canvas for presence of new tag's label in those canvases on creation of new tag
        for canvas in project.canvas_set.all():
            ideas = Idea.objects.filter(canvas=canvas)

            for idea in ideas:

                if tag.label in idea.text:

                    if idea not in tag.idea_set.all():
                        tag.idea_set.add(idea)
                        idea.save()

                        # skip the below step if the above is false
                        if canvas not in tag.canvas_set.all():
                            canvas.save()
                            tag.canvas_set.add(canvas)
                            canvas.save()

                        # save tag if modifications made
                        tag.save()


        tags = CanvasTag.objects.filter(canvas_set__project=project).distinct()
        json_tagged_canvases = []
        json_tagged_ideas = []


        # for t in tags:
        json_tagged_canvases.append(
            serialize(
                'json',
                tag.canvas_set.all().order_by('-id'),
                cls=CanvasEncoder
            )
        )


        json_tagged_ideas.append(
            serialize(
                'json',
                tag.idea_set.all().order_by('canvas'),
                cls=IdeaEncoder
            )
        )

        # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
        json_tag = serialize(
            'json',
            [tag],
            cls = CanvasTagEncoder
        )
        # singular tag - remove enclosing square brackets
        json_tag = json_tag[1:-1]

        data = {
            'function': request.POST['function'],
            'taggedCanvases': json_tagged_canvases,
            'taggedIdeas': json_tagged_ideas,
            'tag': json_tag,
        }

        channel_layer = get_channel_layer()

        room_name = f"{project.pk}_tag"
        room_group_name = 'project_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)


def delete_tag(request):
    '''
    DELETION OF TAG
    '''
    if request.method == 'POST':

        try:
            canvas = Canvas.objects.get(pk=request.POST['canvas_pk'])
            project = canvas.project

        except:
            Canvas.DoesNotExist
            return HttpResponse('Canvas does not exist.', status=404)

            Project.DoesNotExist
            return HttpResponse('Project does not exist.', status=404)

        logged_in_user = request.user
        label = request.POST['label']

        if (not user_permission(logged_in_user, project) or (project.title == 'blank-project')):
            return HttpResponse('Unauthorized', status=401)

        try:
            tag = CanvasTag.objects.get(label=label, canvas_set=canvas)
        except:
            CanvasTag.DoesNotExist
            return HttpResponse('Tag does not exist.', status=404)


        CanvasTag.objects.filter(label=label, canvas_set__project=project).delete()

        # delete any tags that aren't attached to a canvas: they are never useful
        CanvasTag.objects.filter(canvas_set=None).delete()

        # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
        json_tag = serialize(
            'json',
            [tag],
            cls = CanvasTagEncoder
        )
        # singular tag - remove enclosing square brackets
        json_tag = json_tag[1:-1]

        data = {
            'function': request.POST['function'],
            'tag': json_tag,
        }

        channel_layer = get_channel_layer()

        room_name = f"{project.pk}_tag"
        room_group_name = 'project_%s' %room_name

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'channel_message',
                'data': data
            }
        )

        return HttpResponse(status=200)


##################################################################################################################################
#                                                   MISCELLANEOUS FUNCTIONS                                                      #
##################################################################################################################################


def search_canvas_for_tag(tag, canvas):
    '''
    check for presence of tag in canvas
    '''
    ideas = Idea.objects.filter(canvas=canvas)

    for idea in ideas:

        if tag.label in idea.text:

            if idea not in tag.idea_set.all():
                tag.idea_set.add(idea)

                # skip the below step if the above is false
                if canvas not in tag.canvas_set.all():
                    canvas.save()
                    tag.canvas_set.add(canvas)

                # save tag if modifications made
                tag.save()



def user_permission(logged_in_user, project):
    return ((logged_in_user in project.users.all()) or (project.is_public == True))

def admin_permission(logged_in_user, project):
    return ((logged_in_user in project.admins.all()) or (project.is_public == True))

class IdeaEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Idea):
            return str(obj)
        return super().default(obj)

class IdeaCommentEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, IdeaComment):
            return str(obj)
        return super().default(obj)

class CanvasTagEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, CanvasTag):
            return str(obj)
        return super().default(obj)

class CanvasEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Canvas):
            return str(obj)
        return super().default(obj)

class ProjectModelEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Project):
            return str(obj)
        return super().default(obj)

class UserModelEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, CanvasTag):
            return str(obj)
        return super().default(obj)

    class Meta:
        model = User
        exclude = ('password',)
