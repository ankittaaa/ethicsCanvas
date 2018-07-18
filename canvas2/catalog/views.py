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

import django.utils.timezone 


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
        tag.idea_set.remove(idea__canvas__pk=canvas)
        tag.save()

    if (not admin_permission(user, canvas.project) or (project.title == 'blank-project')):
        return { 
                'error': 403,
                'response': 'forbidden'
            }
    
    canvas.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_project(request, pk):
    '''
    Function for deleting a canvas
    '''
    user = request.user
    project = Project.objects.get(pk = pk)

    if (not admin_permission(user, project) or (project.title == 'blank-project')):
        return { 
                'error': 403,
                'response': 'forbidden'
            }
        
    canvas.delete()
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
                tag = CanvasTag(label=None)
                # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
                json_tags = serialize(
                    'json', 
                    [tag], 
                    cls = CanvasTagEncoder
                )
                # singular tag, replace enclosing square brackets with curly brackets
                json_tags = json_tags[1:-1]
                # json_tags = '{' + json_tags + '}'

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
                    [tag], 
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

def new_trial_idea(logged_in_user, canvas_pk, category):
    try:
        canvas = Canvas.objects.get(pk = canvas_pk)
    except Canvas.DoesNotExist:
        return error

    project = canvas.project
    # can't add ideas if the canvas is unavailable or if the blank canvas is being edited to by an authenticated user
    if (not user_permission(logged_in_user, project) and ('blank-' not in canvas.title and logged_in_user.is_authenticated)):
        return { 
                'error': 401,
                'response': 'unauthorized'
            }
        
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

    data = {
        'return_idea': return_idea,
        'pk': idea.pk
    }

    return data

def delete_trial_idea(idea_pk):
    Idea.objects.get(pk=idea_pk).delete()



def new_idea(logged_in_user, canvas_pk, category):
    '''
    Creation of a new idea. This gets the id for the canvas in which it is created from the calling URL
    '''
    try:
        canvas = Canvas.objects.get(pk = canvas_pk)
        project = canvas.project
    except:
        Canvas.DoesNotExist
        return {
            'error': 'Canvas does not exist'
        }

        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }

    # can't add ideas if the canvas is unavailable or if the blank canvas is being edited to by an authenticated user
    if (not user_permission(logged_in_user, project) and ('blank-' not in canvas.title and logged_in_user.is_authenticated)):
        return { 
                'error': 401,
                'response': 'unauthorized'
            }
        
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


    return {
        'return_idea': return_idea,
        'error': None
    }







def delete_idea(logged_in_user, idea_pk):
    '''
    Deletion of an idea 
    '''
    try:
        idea = Idea.objects.get(pk=idea_pk)
        canvas = idea.canvas
        project = canvas.project

    except:
        Idea.DoesNotExist
        return {
            'error': 'Comment does not exist'
        }

        Canvas.DoesNotExist
        return {
            'error': 'Canvas does not exist'
        }

        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }

    # can't remove ideas if the canvas is unavailable or if the blank canvas is being edited by an authenticated user
    if (not user_permission(logged_in_user, project) and ('blank-' not in canvas.title and logged_in_user.is_authenticated)):
        return { 
                'error': 401,
                'response': 'unauthorized'
            }

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


    return{
        'return_tag_data': return_tag_data,
        'idea': return_idea,
        'category': category,
        'error': None
    }



def edit_idea(logged_in_user, idea_pk, input_text):
    '''
    Update of an idea
    '''
    try:
        idea = Idea.objects.get(pk = idea_pk)
        canvas = idea.canvas
        project = canvas.project
    
    except:
        Idea.DoesNotExist
        return {
            'error': 'Comment does not exist'
        }

        Canvas.DoesNotExist
        return {
            'error': 'Canvas does not exist'
        }

        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }
    current_tags_in_idea = idea.tags.all()

    old_text = idea.text

    if (not user_permission(logged_in_user, project) or (project.title == 'blank-project')):
        return { 
                'error': 401,
                'response': 'unauthorized'
            }

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



    for tag in updated_tags_in_idea:

        new_tags=(
            serialize(
                'json', 
                [tag], 
                cls = CanvasTagEncoder
            )
        )

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

    # singular idea, remove enclosing square brackets
    return_idea = return_idea[1:-1]


    return {
        'removed_return_tag_data': removed_return_tag_data,
        'new_return_tag_data': new_return_tag_data,
        'return_idea': return_idea,
        'old_text': old_text,
        'error': None
    }



##################################################################################################################################
#                                                       COMMENT VIEWS                                                            #
################################################################################################################################## 


def new_comment(input_text, idea_pk, logged_in_user):
    
    try:
        idea = Idea.objects.get(pk = idea_pk)
        canvas = idea.canvas
        project = canvas.project

    except:
        Idea.DoesNotExist
        return {
            'error': 'Comment does not exist'
        }

        Canvas.DoesNotExist
        return {
            'error': 'Canvas does not exist'
        }

        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }

    if (not user_permission(logged_in_user, project) or (project.title == 'blank-project')):
        return { 
                'error': 401,
                'response': 'unauthorized'
            }

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


    return {
        'comment': json_comment,
        'category': idea.category,
        'error': None
    }


def delete_comment(logged_in_user, comment_pk):
    '''
    Deletion of a comment
    '''
    try:
        comment = IdeaComment.objects.get(pk = comment_pk)
        canvas = comment.idea.canvas
        project = canvas.project

    except:
        IdeaComment.DoesNotExist
        return {
            'error': 'Comment does not exist'
        }

        Canvas.DoesNotExist
        return {
            'error': 'Canvas does not exist'
        }

        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }

    if (not admin_permission(logged_in_user, project) or (project.title == 'blank-project')):
        return { 
                'error': 403,
                'response': 'forbidden'
            }
  
    category = comment.idea.category
    comment.delete()

    return {
        'category': category,
        'error': None
    }

def single_comment_resolve(logged_in_user, comment_pk):
    '''
    Resolution of a single comment
    '''
    try:
        comment = IdeaComment.objects.get(pk = comment_pk)
        canvas = comment.idea.canvas
        project = canvas.project

    except:
        IdeaComment.DoesNotExist
        return {
            'error': 'Comment does not exist'
        }

        Canvas.DoesNotExist
        return {
            'error': 'Canvas does not exist'
        }

        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }


    if (not admin_permission(logged_in_user, project) or (project.title == 'blank-project')):
        return { 
                'error': 403,
                'response': 'forbidden'
            }
  
    category = comment.idea.category
    comment.resolved = True
    comment.save()

    return {
        'category': category,
        'error': None
    }


def all_comment_resolve(logged_in_user, idea_pk):
    '''
    Resolution of comments - mark all as resolved
    '''
    try: 
        idea = Idea.objects.get(pk = idea_pk)
        canvas = idea.canvas
        project = canvas.project
    except:
        Idea.DoesNotExist
        return {
            'error': 'Comment does not exist'
        }

        Canvas.DoesNotExist
        return {
            'error': 'Canvas does not exist'
        }

        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }

    if (not admin_permission(logged_in_user, project) or (project.title == 'blank-project')):
        return { 
                'error': 403,
                'response': 'forbidden'
            }
    
    IdeaComment.objects.all().filter(idea = idea).update(resolved=True)
    

    return {
        'category': idea.category,
        'error': None
    }
        

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
        
def add_user(logged_in_user, project_pk, name):
    '''
    Function for addition of user to project
    '''
    try:
        project = Project.objects.get(pk=project_pk)
    except:
        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }

    name = name
    

    if (not admin_permission(logged_in_user, project)):
        return { 
                'error': 403,
                'response': 'forbidden'
            }

    else:
        user = User.objects.get(username=name)

        if not user:
            reply = 'Error: ' + name + ' does not exist. Please try a different username.'
            return { 
                'error': 500,
                'response': reply
            }

        if user in project.users.all() or user in project.admins.all():
            reply = ''

            if user is logged_in_user:
                reply = 'Error: you\'re already a collaborator, you can\'t add yourself!'

            else:
                reply = 'Error: ' + name + ' is already a collaborator!'
        
            return { 
                'error': 500,
                'response': reply
            }

        project.users.add(user)

        # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
        json_user = serialize(
            'json', 
            [user],
            cls = UserModelEncoder
        )
        # singular user - remove enclosing square brackets
        json_user = json_user[1:-1]

        return {
            'json_user': json_user,
            'error': None
        }

def delete_user(logged_in_user, project_pk, user_pk):
    '''
    Function for deleting a user from the project.
    '''
    try:
        project = Project.objects.get(pk=project_pk)
    except:
        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }
    

    if (not admin_permission(logged_in_user, project)):
        return { 
                'error': 403,
                'response': 'forbidden'
            }


    user = User.objects.get(pk = user_pk)

    if user not in project.users.all():
        reply = 'Error: ' + name + ' is not a collaborator'
        return { 
                'error': 500,
                'response': reply
            }

    admins = project.admins.all()

    # if there is one admin who is the logged-in user, do not allow them to 
    # delete themselves. It's implied that if there's one admin, the logged_in 
    # user is that admin, as earlier it is checked that the logged_in user
    # is in the project admin set
    if (len(admins) == 1 and user in admins):
        reply = 'Error: You are the only admin, you may not delete yourself!'
        return { 
                'error': 500,
                'response': reply
            }

    victim_is_admin = "false"
    # if the user is also an admin, remove them from that field also
    if user in admins:
        victim_is_admin = "true"
        project.admins.remove(user)      

    project.users.remove(user)

    return {
        'victim_is_admin': victim_is_admin,
        'error': None
    }


def promote_user(logged_in_user, project_pk, user_pk):
    '''
    Function for promoting a user to admin status
    '''
    try:
        project = Project.objects.get(pk=project_pk)
    except:
        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }
    

    # check is admin
    if (not admin_permission(logged_in_user, project)):
            return { 
                    'error': 403,
                    'response': 'forbidden'
                }

    user = User.objects.get(pk = user_pk)
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
        
        return { 
                'error': 500,
                'response': reply
            }

    project.admins.add(user)

    # TODO: change serialization method from needing to pass a singleton list to accepting a single model instance
    json_user = serialize(
        'json', 
        [user],
        cls = UserModelEncoder
    )
    # singular user - remove enclosing square brackets
    json_user = json_user[1:-1]

    return {
        'json_user': json_user,
        'error': None
    }


def demote_user(logged_in_user, project_pk, user_pk):
    '''
    Function to delete a user from the admin field - this is for demotion only.
    For complete deletion, call delete user
    '''
    try:
        project = Project.objects.get(pk=project_pk)
    except:
        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }
    
    if (not admin_permission(logged_in_user, project)):
        return { 
                'error': 403,
                'response': 'forbidden'
            }

    user = User.objects.get(pk = user_pk)
    admins = project.admins.all()
    # Can't delete a non-existent admin
    if user not in admins:
        reply = 'Error: ' + name + ' is not an admin'
        return { 
                'error': 500,
                'response': reply
            }

    # if there is one admin who is the logged-in user, do not allow them to 
    # delete themselves
    if len(admins) == 1:
        reply = 'Error: You are the only admin, you may not demote yourself!'
        return { 
                'error': 500,
                'response': reply
            }

    project.admins.remove(user)

    return {
        'error': None
    }


def toggle_public(project_pk, logged_in_user):
    project = Project.objects.get(pk=project_pk)


    if (not admin_permission(logged_in_user, project)):
        return { 
                'error': 403,
                'response': 'forbidden'
            }

    project.is_public = not(project.is_public)
    project.save()

    return {
        'error': None
    }





##################################################################################################################################
#                                                           TAG VIEWS                                                            #
##################################################################################################################################

def add_tag(canvas_pk, logged_in_user, label):
    '''
    ADDITION OF NEW TAG 
    '''
    try: 
        canvas = Canvas.objects.get(pk=canvas_pk)
    except:
        Canvas.DoesNotExist
        return {
            'error': 'Canvas does not exist'
        }
    # idea = Idea.objects.get(pk=idea_pk)

    try:
        project = canvas.project
    except:
        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }



    if (not user_permission(logged_in_user, project) or (project.title == 'blank-project')):
        return { 
                'error': 401,
                'response': 'unauthorized'
            }

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
        'taggedCanvases': json_tagged_canvases,
        'taggedIdeas': json_tagged_ideas,
        'tag': json_tag,
    }

    return {
        'data': data,
        'error': None
    }


def delete_tag(canvas_pk, logged_in_user, label):
    '''
    DELETION OF TAG
    '''
    try: 
        canvas = Canvas.objects.get(pk=canvas_pk)
    except:
        Canvas.DoesNotExist
        return {
            'error': 'Canvas does not exist'
        }
    # idea = Idea.objects.get(pk=idea_pk)

    try:
        project = canvas.project
    except:
        Project.DoesNotExist
        return {
            'error': 'Project does not exist'
        }

    if (not user_permission(logged_in_user, project) or (project.title == 'blank-project')):
        return { 
                'error': 401,
                'response': 'unauthorized'
            }

    try:
        tag = CanvasTag.objects.get(label=label, canvas_set=canvas)
    except:
        CanvasTag.DoesNotExist
        return {
            'error': 'Tag does not exist'
        }

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


    return {
        'tag': json_tag,
        'error': None
    }


##################################################################################################################################
#                                                   MISCELLANEOUS FUNCTIONS                                                      #
################################################################################################################################## 



# def get_canvases_accessible_by_user(logged_in_user, project):
#     '''
#     function to get every canvas accessible to the currently logged-in user
#     '''
#     all_canvases = Canvas.objects.filter(project=project)
    
#     json_all_canvases = serialize(
#         'json', 
#         all_canvases,
#         cls=CanvasEncoder
#     )   

#     data = {
#         'all_canvases': json_all_canvases
#     }

#     return data

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

