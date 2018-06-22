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


# TODO: Create permissions for actions (add/remove users, delete canvas...)
import django.utils.timezone 





##################################################################################################################################
#                                                           CANVAS VIEWS                                                         #
##################################################################################################################################

 

def new_canvas(request, canvas_type):
    creator = request.user
    canvas_is_ethics = True
    split_url = request.META.get('HTTP_REFERER').split('/')
    project_pk = split_url[len(split_url) - 2]
    project = Project.objects.get(pk=project_pk)

    if canvas_type == 0:
        canvas_is_ethics = False

    if creator.is_authenticated:

        # canvas_is_ethics bool = true for ethics, false for business 
        canvas = Canvas(is_ethics=canvas_is_ethics, project=project)
        canvas.save()
        canvas.title = f'New Canvas {canvas.pk} (Ethics)' if canvas_is_ethics else f'New Canvas {canvas.pk} (Business)'   

        # canvas.admins.add(creator)
        # canvas.users.add(creator)
        canvas.save()

        return redirect(canvas.get_absolute_url()) # bring user to the canvas page for the newly created canvas
    else :
        # check that a blank canvas exists - this will be used to render a blank canvas for the anonymous user to interact with
        if canvas_is_ethics:
            if Canvas.objects.filter(title='blank-ethics').exists():
                return redirect(Canvas.objects.get(title='blank-ethics').get_absolute_url()) 
            else :
            # if there is no blank canvas, create one. set public to false so that it remains blank
                canvas = Canvas(title='blank-ethics', is_ethics=True)
                canvas.save()
                return redirect(canvas.get_absolute_url()) # bring user to the canvas page for the newly created canvas  
        else: 
            if Canvas.objects.filter(title='blank-business').exists():
                return redirect(Canvas.objects.get(title='blank-business').get_absolute_url()) 
            else :
            # if there is no blank canvas, create one. set public to false so that it remains blank
                canvas = Canvas(title='blank-business', is_ethics=False)
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

    if (not admin_permission(user, canvas.project) or ('blank-' in canvas.title)):
        return HttpResponse('Forbidden', status = 403)
        
    canvas.delete()
    return redirect(request.META.get('HTTP_REFERER'))

def delete_project(request, pk):
    '''
    Function for deleting a canvas
    '''
    user = request.user
    project = Project.objects.get(pk = pk)

    if (not admin_permission(user, project) or ('blank-' in canvas.title)):
        return HttpResponse('Forbidden', status = 403)
        
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

        # public canvases are those where public is true
        public = Project.objects.filter(**filter_kwargs)
        # private canvases where the user is either the owner or a collaborator on the canvas
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

        # json_public = serialize(
        #     'json', 
        #     public,
        #     cls=CanvasEncoder
        # )

        # json_private = serialize(
        #     'json', 
        #     my_private,
        #     cls=CanvasEncoder
        # )

        # json_all_projects = serialize(
        #     'json', 
        #     all_projects,
        #     cls=CanvasEncoder
        # )
        # print(my_private)

        # self.request.session['public_projects'] = json_public
        # self.request.session['private_projects'] = json_private
        # self.request.session['all_projects'] = json_all_projects

        return context

class ProjectDetailView(generic.DetailView):
    model = Project

    def get(self, request, pk):

        logged_in_user = self.request.user 
        project = Project.objects.get(pk=pk)

        if (not user_permission(logged_in_user, project)):
            return HttpResponse('Unauthorized', status = 401)

        if request.is_ajax():
            json_users = '""'
            json_admins = '""'

            users = project.users.all()
            admins = project.admins.all()
            current = [logged_in_user]

            update_canvas_session_variables(self, logged_in_user, project)

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
            return HttpResponse('Unauthorized', status = 401)

        if request.is_ajax():
            json_comments = '""'
            json_ideas = '""'
            json_tags = '""'
            json_self = '""'

            if (logged_in_user.is_authenticated):
                update_canvas_session_variables(self, logged_in_user, project)

                current = [logged_in_user]
                all_canvases = request.session['all_canvases']
            
            else:
                current = project.users.none()
                comments = "''"
                all_canvases = "''"


            ideas = Idea.objects.filter(canvas = canvas)
            tags = canvas.tags.all()
            all_tags = CanvasTag.objects.filter(canvas_set__in=Canvas.objects.filter(project=project)).distinct()
            all_tagged_canvasses_json = []

            for i in range(len(all_tags)):
                all_tagged_canvasses_json.append(serialize(
                        'json',
                        Canvas.objects.filter(tags=all_tags[i]),
                        cls=CanvasEncoder
                    ))

            comments = IdeaComment.objects.filter(idea__in=ideas)
            
            if tags:
                json_tags = serialize(
                    'json', 
                    tags, 
                    cls = CanvasTagEncoder
                )

            else: 
                tag = CanvasTag(label=None)
                json_tags = serialize(
                    'json', 
                    [tag], 
                    cls = CanvasTagEncoder
                )

            if all_tags:
                json_all_tags = serialize(
                    'json', 
                    all_tags, 
                    cls = CanvasTagEncoder
                )

            else: 
                tag = CanvasTag(label=None)
                json_all_tags = serialize(
                    'json', 
                    [tag], 
                    cls = CanvasTagEncoder
                )

            if comments:
                json_comments = serialize(
                    'json',
                    comments,
                    cls = IdeaCommentEncoder
                )


            json_self=serialize(
                'json',
                current,
                cls=UserModelEncoder
            )

            json_canvas=serialize(
                'json',
                [canvas],
                cls=CanvasEncoder
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
                'allTaggedCanvasses': all_tagged_canvasses_json,
                # 'public': public_canvases,
                # 'private': private_canvases,
                'allCanvasses': all_canvases,
                'thisCanvas': json_canvas,
                'isEthics': canvas.is_ethics,
                'projectPK': project.pk,

            }

            return JsonResponse(data, safe = False)
        else:
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



# TODO: USER PERMISSION REQUIRED

def new_idea(logged_in_user, canvas_pk, category):
    '''
    Creation of a new idea. This gets the id for the canvas in which it is created from the calling URL
    '''
    try:
        canvas = Canvas.objects.get(pk = canvas_pk)
    except Canvas.DoesNotExist:
        return error

    project = canvas.project
    # can't add ideas if the canvas is unavailable or if the blank canvas is being edited to by an authenticated user
    if (not user_permission(logged_in_user, project) and ('blank-' not in canvas.title and logged_in_user.is_authenticated)):
        return HttpResponse('Unauthorized', status = 401)
        
    idea = Idea(
        canvas = canvas, 
        category = category, 
        text = ''
    )
    idea.save()
    # This is so I can click on it in the django admin - should probably delete later
    idea.title = f'Canvas {canvas_pk} Idea {idea.pk}'
    idea.save()

    return_idea = serialize(
        'json', 
        [idea], 
        cls=IdeaEncoder
    )

    data = {
        'return_idea': return_idea,
        'pk': idea.pk
    }

    return data


def delete_idea(logged_in_user, idea_pk):
    '''
    Deletion of an idea 
    '''
    idea = Idea.objects.get(pk = idea_pk)
    canvas = idea.canvas
    project = canvas.project

    # can't remove ideas if the canvas is unavailable or if the blank canvas is being edited by an authenticated user
    if (not user_permission(logged_in_user, project) and ('blank-' not in canvas.title and logged_in_user.is_authenticated)):
        return HttpResponse('Unauthorized', status = 401)

    category = idea.category
    idea.delete()

    return category



# TODO: USER PERMISSION REQUIRED
def idea_detail(logged_in_user, idea_pk, input_text):
    '''
    Update of an idea
    '''
    idea = Idea.objects.get(pk = idea_pk)
    old_text = idea.text
    canvas = idea.canvas
    project = canvas.project

    if (not user_permission(logged_in_user, project) or ('blank-' in canvas.title)):
        return HttpResponse('Unauthorized', status = 401)

    input_text = strip_tags(input_text)

    idea.text = input_text
    idea.save()

    return_idea = serialize(
        'json', 
        [idea], 
        cls=IdeaEncoder
    )

    return {
        'return_idea': return_idea,
        'old_text': old_text
    }



##################################################################################################################################
#                                                       COMMENT VIEWS                                                            #
################################################################################################################################## 



def comment_thread(request, pk):
    '''
    View function for displaying the comment thread of an idea, and for posting a new comment
    Still have it as a GET as it remains to be a navigation away from current page to comment page
    '''
    idea = Idea.objects.get(pk = pk)
    canvas = idea.canvas
    logged_in_user = request.user
    project = canvas.project

    if (not user_permission(logged_in_user, project) or ('blank-' in canvas.title)):
        return HttpResponse('Unauthorized', status = 401)

    if request.method == 'POST':
        comments = IdeaComment.objects.filter(idea = idea)
        users = []

        for comment in comments:
            users.append(comment.user.username)
        
        json_comments = serialize(
            'json', 
            comments, 
            cls = IdeaCommentEncoder
        )

        data = {
            'comments': json_comments,
            'authors': users
        }
        return JsonResponse(data, safe = False)


def new_comment(input_text, idea_pk, logged_in_user):
    
    idea = Idea.objects.get(pk = idea_pk)
    canvas = idea.canvas
    project = canvas.project

    if (not user_permission(logged_in_user, project) or ('blank-' in canvas.title)):
        return HttpResponse('Unauthorized', status = 401)

    text = input_text
    text = strip_tags(text)

    comment = IdeaComment(
        user = logged_in_user, 
        text = text,
        idea = idea
    )
    comment.save()

    json_comment = serialize(
        'json',
        [comment],
        cls = IdeaCommentEncoder
    )

    data = {
        'comment': json_comment,
        'category': idea.category,
    }

    return data

# TODO: ADMIN PERMISSION REQUIRED
def delete_comment(logged_in_user, comment_pk):
    '''
    Deletion of a comment
    '''
    comment = IdeaComment.objects.get(pk = comment_pk)
    canvas = comment.idea.canvas
    project = canvas.project

    if (not admin_permission(logged_in_user, project) or ('blank-' in canvas.title)):
        return HttpResponse('Forbidden', status = 403)
  
    category = comment.idea.category
    comment.delete()

    return category


# TODO: ADMIN PERMISSION REQUIRED
def comment_resolve(logged_in_user, idea_pk):
    '''
    Resolution of comments - mark all as resolved
    '''
    idea = Idea.objects.get(pk = idea_pk)
    canvas = idea.canvas
    project = canvas.project

    if (not admin_permission(logged_in_user, project) or ('blank-' in canvas.title)):
        return HttpResponse('Forbidden', status = 403)
    
    IdeaComment.objects.all().filter(idea = idea).update(resolved=True)

    return idea.category
        

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

    project = Project.objects.get(pk=project_pk)
    

    if (not admin_permission(logged_in_user, project)):
        return HttpResponse('Unauthorized', status = 401)

    else:
        user = User.objects.get(username = name)

        if not user:
            reply = 'Error: ' + name + ' does not exist. Please try a different username.'
            return HttpResponse(reply, status = 500)

            if logged_in_user in project.users.all() or user in project.admins.all():
                reply = ''

            if user is logged_in_user:
                reply = 'Error: you\'re already a collaborator, you can\'t add yourself!'
            else:
                reply = 'Error: ' + name + ' is already a collaborator!'

            return HttpResponse(reply, status = 500)

        project.users.add(user)

        json_user = serialize(
            'json', 
            [user],
            cls = UserModelEncoder
        )
        
        return json_user

def delete_user(logged_in_user, project_pk, user_pk):
    '''
    Function for deleting a user from the project.
    '''
    project = Project.objects.get(pk=project_pk)
    

    if (not admin_permission(logged_in_user, project)):
        return HttpResponse('Forbidden', status = 403)


    user = User.objects.get(pk = user_pk)

    if user not in project.users.all():
        reply = 'Error: ' + name + ' is not a collaborator'
        return HttpResponse(reply, status = 500)

    admins = project.admins.all()

    # if there is one admin who is the logged-in user, do not allow them to 
    # delete themselves. It's implied that if there's one admin, the logged_in 
    # user is that admin, as earlier it is checked that the logged_in user
    # is in the project admin set
    if (len(admins) == 1 and user in admins):
        reply = 'Error: You are the only admin, you may not delete yourself!'
        return HttpResponse(reply, status = 500)

    victim_is_admin = "false"
    # if the user is also an admin, remove them from that field also
    if user in admins:
        victim_is_admin = "true"
        project.admins.remove(user)      

    project.users.remove(user)

    return victim_is_admin



def promote_user(logged_in_user, project_pk, user_pk):
    '''
    Function for promoting a user to admin status
    '''
    project = Project.objects.get(pk=project_pk)
    

    # check is admin
    if (not admin_permission(logged_in_user, project)):
        return HttpResponse('Forbidden', status = 403)

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
        
        return HttpResponse(reply, status = 500)

    project.admins.add(user)

    json_user = serialize(
        'json', 
        [user],
        cls = UserModelEncoder
    )
    
    return json_user


def demote_user(logged_in_user, project_pk, user_pk):
    '''
    Function to delete a user from the admin field - this is for demotion only.
    For complete deletion, call delete user
    '''
    project = Project.objects.get(pk=project_pk)
    
    
    if (not admin_permission(logged_in_user, project)):
        return HttpResponse('Forbidden', status = 403)

    user = User.objects.get(pk = user_pk)
    admins = project.admins.all()
    # Can't delete a non-existent admin
    if user not in admins:
        reply = 'Error: ' + name + ' is not an admin'
        return HttpResponse(reply, status = 500)

    # if there is one admin who is the logged-in user, do not allow them to 
    # delete themselves
    if len(admins) == 1:
        reply = 'Error: You are the only admin, you may not demote yourself!'
        return HttpResponse(reply, status = 500)

    project.admins.remove(user)


def toggle_public(project_pk, logged_in_user):
    project = Project.objects.get(pk=project_pk)


    if (not admin_permission(logged_in_user, project)):
        return HttpResponse('Forbidden', status = 403)

    project.is_public = not(project.is_public)
    project.save()





##################################################################################################################################
#                                                           TAG VIEWS                                                            #
##################################################################################################################################

def add_tag(canvas_pk, logged_in_user, label):
    '''
    ADDITION OF NEW TAG 
    '''
    canvas = Canvas.objects.get(pk=canvas_pk)
    project = canvas.project

    if (not user_permission(logged_in_user, project) or ('blank-' in canvas.title)):
        return HttpResponse('Forbidden', status = 403)

    # check existence of tag within project - avoid duplicating tags
    if CanvasTag.objects.filter(label=label, canvas_set__project=project).exists():
        tag = CanvasTag.objects.get(label=label)

        tag_canvas_set = tag.canvas_set.all()

        if canvas in tag_canvas_set:
            print("Oh shit what are you doing it exists already haha")
        else:
            tag.canvas_set.add(canvas)
            tag.save()

    else:
        # only create tag if it doesn't exist anywhere visible to the user
        tag = CanvasTag(label=label)
        tag.save()
        tag.canvas_set.add(canvas)
        tag.save()




    data = get_canvases_accessible_by_user(logged_in_user, project)

    # check every canvas for presence of new tag's label in those canvases on creation of new tag
    for c in serializers.deserialize("json", data['all_canvases']):
        search_canvas_for_tag(tag, c.object.pk, "add")

    tagged_canvases = Canvas.objects.filter(tags__label__contains=tag.label, project=project)

    json_tagged_canvases = serialize(
        'json', 
        tagged_canvases,
        cls=CanvasEncoder
    )

    json_tag = serialize(
        'json', 
        [tag], 
        cls = CanvasTagEncoder
    )

    return_data = {
        'taggedCanvasses': json_tagged_canvases,
        'allCanvasses': data['all_canvases'],
        'tag': json_tag,
    }

    return return_data
 

def remove_tag(tag_pk, logged_in_user, canvas_pk):
    '''
    REMOVAL OF TAG - triggered by occurrences of that tag in a canvas reaching zero
    '''
    canvas = Canvas.objects.get(pk=canvas_pk)
    tag = CanvasTag.objects.get(pk=tag_pk)
    # print(canvas)

    canvas.tags.remove(tag)
    tag.canvas_set.remove(canvas)

    # print(tag.canvas_set.all())
    canvas.save()

    # delete any tags that aren't attached to a canvas: they are never useful
    CanvasTag.objects.filter(canvas_set=None).delete()


    data = get_canvases_accessible_by_user(logged_in_user, canvas.project)

    # check every canvas for presence of new tag's label in those canvases on creation of new tag
    # for c in serializers.deserialize("json", data['all_canvases']):
        # search_canvas_for_tag(tag, c.object.pk, "delete")

    tagged_canvases = Canvas.objects.filter(tags__label__contains=tag.label)
    # print(tagged_canvases)

    json_tagged_canvases = serialize(
        'json', 
        tagged_canvases,
        cls=CanvasEncoder
    )

    json_tag = serialize(
        'json', 
        [tag], 
        cls = CanvasTagEncoder
    )

    return_data = {
        'taggedCanvasses': json_tagged_canvases,
        'allCanvasses': data['all_canvases'],
        'tag': json_tag,
    }

    return return_data


def delete_tag(tag_pk, canvas_pk):
    '''
    DELETION OF TAG
    '''
    canvas = Canvas.objects.get(pk=canvas_pk)
    tag = CanvasTag.objects.get(pk=tag_pk)
    CanvasTag.objects.get(pk=tag_pk).delete()

    # delete any tags that aren't attached to a canvas: they are never useful
    CanvasTag.objects.filter(canvas_set=None).delete()

    json_tag = serialize(
        'json', 
        [tag], 
        cls = CanvasTagEncoder
    )

    return json_tag


##################################################################################################################################
#                                                   MISCELLANEOUS FUNCTIONS                                                      #
################################################################################################################################## 



def get_canvases_accessible_by_user(logged_in_user, project):
    '''
    function to get every canvas accessible to the currently logged-in user
    '''
    # filter_kwargs = {'is_public': True}
    # user_filter_kwargs = {'users': logged_in_user}
    # admin_filter_kwargs = {'admins': logged_in_user}

    # # canvases = Canvas.objects.all()

    # # public canvases are those where public is true
    # public_projects = Project.objects.filter(**filter_kwargs)
    # # private canvases where the user is either the owner or a collaborator on the canvas
    # private_projects = Project.objects.exclude(**filter_kwargs)

    # my_private_projects = (
    #     private_projects.filter(**admin_filter_kwargs) | private_projects.filter(**user_filter_kwargs)
    # ).distinct()

    # all_projects = (
    #     Project.objects.filter(**filter_kwargs) | private_projects.filter(**admin_filter_kwargs) | private_projects.filter(**user_filter_kwargs)
    # ).distinct()

    # public = Canvas.objects.filter(project__in=public_projects)
    # my_private = Canvas.objects.filter(project__in=my_private_projects)
    # all_canvases = Canvas.objects.filter(project__in=all_projects)



    # json_public = serialize(
    #     'json', 
    #     public,
    #     cls=CanvasEncoder
    # )

    # json_private = serialize(
    #     'json', 
    #     my_private,
    #     cls=CanvasEncoder
    # )
    all_canvases = Canvas.objects.filter(project=project)
    
    json_all_canvases = serialize(
        'json', 
        all_canvases,
        cls=CanvasEncoder
    )   

    data = {
        # 'public': json_public,
        # 'my_private': json_private,
        'all_canvases': json_all_canvases
    }

    return data

def update_canvas_session_variables(self, logged_in_user, project):
    data = get_canvases_accessible_by_user(logged_in_user, project)

    # self.request.session['public_canvases'] = data['public']
    # self.request.session['private_canvases'] = data['my_private']
    self.request.session['all_canvases'] = data['all_canvases']

    # NOTE END: BAND-AID FOR UPDATING SESSION DATA ON LOAD

def search_canvas_for_tag(tag, canvas_pk, operation):
    '''
    check for presence of tag in canvas 
    don't need cardinality, only need presence
    cardinality is already handled on JS side 
    '''
    canvas = Canvas.objects.get(pk=canvas_pk)
    ideas = Idea.objects.filter(canvas=canvas_pk)

    for i in ideas:
        if tag.label in i.text:
            if operation == 'add':
                canvas.tags.add(tag)
                canvas.save()
                tag.save()
                return

            elif operation == 'delete':
                canvas.tags.remove(tag)
                return


def user_permission(logged_in_user, project):
    return ((logged_in_user in project.users.all()) or (project.is_public == True))

def admin_permission(logged_in_user, project):
    return (logged_in_user in project.admins.all())

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

