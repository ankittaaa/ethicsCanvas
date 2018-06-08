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
from django.utils.html import strip_tags
from django.db.models import Q
from channels.db import database_sync_to_async
from django.db.models.query import EmptyQuerySet

from .models import Canvas, CanvasTag, Idea, IdeaComment
from .forms import SignUpForm, IdeaForm, CommentForm, AddUserForm


# TODO: Create permissions for actions (add/remove users, delete canvas...)
import django.utils.timezone 





##################################################################################################################################
#                                                           CANVAS VIEWS                                                         #
##################################################################################################################################

 

def new_canvas(request):
    creator = request.user

    if creator.is_authenticated:

        canvas = Canvas(is_public = False, owner = creator)
        canvas.save()
        canvas.title = f'New Canvas {canvas.pk}'   

        canvas.admins.add(creator)
        canvas.users.add(creator)
        canvas.save()

        return redirect(canvas.get_absolute_url()) # bring user to the canvas page for the newly created canvas
    else :
        # check that a blank canvas exists - this will be used to render a blank canvas for the anonymous user to interact with
        if Canvas.objects.filter(title='blank').exists():
            return redirect(Canvas.objects.get(title='blank').get_absolute_url()) 
        else :
            # if there is no blank canvas, create one. set public to false so that it remains blank
            canvas = Canvas(is_public = False, title='blank')
            canvas.save()
            return redirect(canvas.get_absolute_url()) # bring user to the canvas page for the newly created canvas  




def delete_canvas(request, pk):
    '''
    Function for deleting a canvas
    '''
    user = request.user
    canvas = Canvas.objects.get(pk = pk)

    if (not admin_permission(logged_in_user, canvas)) or (canvas.title == 'blank'):
        return HttpResponse('Forbidden', status = 403)
        
    canvas.delete()
    return redirect(request.META.get('HTTP_REFERER'))


##################################################################################################################################
#                                                   CANVAS CLASS-BASED VIEWS                                                     #
##################################################################################################################################


class CanvasList(LoginRequiredMixin, generic.ListView):
    model = Canvas

    def get_context_data(self, **kwargs):
        '''
        This function's purpose is to separate the public from the private canvasses
        '''
        me = self.request.user
        context = super().get_context_data(**kwargs)

        filter_kwargs = {'is_public': True}
        user_filter_kwargs = {'users': me}
        admin_filter_kwargs = {'admins': me}

        canvasses = Canvas.objects.all()

        # public canvasses are those where public is true
        public = canvasses.filter(**filter_kwargs)
        # private canvasses where the user is either the owner or a collaborator on the canvas
        private = canvasses.exclude(**filter_kwargs)

        my_private = (
            private.filter(**admin_filter_kwargs) | private.filter(**user_filter_kwargs)
        ).distinct()

        all_canvasses = (
            canvasses.filter(**filter_kwargs) | private.filter(**admin_filter_kwargs) | private.filter(**user_filter_kwargs)
        ).distinct()

        context['public_canvas_list'] = public
        context['private_canvas_list'] = my_private
        context['all_canvas_list'] = all_canvasses

        json_public = serialize(
            'json', 
            public,
            cls=CanvasEncoder
        )

        json_private = serialize(
            'json', 
            my_private,
            cls=CanvasEncoder
        )

        json_all_canvasses = serialize(
            'json', 
            all_canvasses,
            cls=CanvasEncoder
        )

        self.request.session['public'] = json_public
        self.request.session['private'] = json_private
        self.request.session['all_canvasses'] = json_all_canvasses

        return context



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

        # if not logged_in_user.is_authenticated and canvas.title == 'blank':

        if (not user_permission(logged_in_user, canvas) and canvas.title != 'blank' and logged_in_user.is_authenticated):
            return HttpResponse('Unauthorized', status = 401)

        if request.is_ajax():
            json_users = '""'
            json_admins = '""'
            json_comments = '""'
            json_ideas = '""'
            json_tags = '""'
            json_self = '""'

            if (logged_in_user.is_authenticated):
                update_canvas_session_variables(self, logged_in_user)

                users = canvas.users.all()
                admins = canvas.admins.all()
                current = [logged_in_user]
                

                public_canvasses = request.session['public']
                private_canvasses = request.session['private']
                all_canvasses = request.session['all_canvasses']
            
            else:
                users = canvas.users.none()
                admins = canvas.users.none()
                current = canvas.users.none()
                

                comments = "''"
                public_canvasses  ="''"
                private_canvasses = "''"
                all_canvasses = "''"


            ideas = Idea.objects.filter(canvas = canvas)
            tags = canvas.tags.all()
            comments = IdeaComment.objects.filter(idea__in=ideas)
            
            if tags:
                json_tags = serialize(
                    'json', 
                    tags, 
                    cls = CanvasTagEncoder
                )

            if comments:
                json_comments = serialize(
                    'json',
                    comments,
                    cls = IdeaCommentEncoder
                )

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

        
        # NOTE: Removed comments, users and admins. These are all
        # serialised and sent to browser in different views
            
        
        # these already exist in JSON form

            
            if ideas:
            # only serialise ideas if they exist
                json_ideas = serialize(
                    'json', 
                    ideas, 
                    cls = IdeaEncoder
                )


            data = {
                'ideas': json_ideas,
                'comments': json_comments,
                'tags': json_tags,
                'admins': json_admins,
                'users': json_users,
                'loggedInUser': json_self,
                'public': public_canvasses,
                'private': private_canvasses,
                'allCanvasses': all_canvasses

            }

            return JsonResponse(data, safe = False)
        else:
            return render(
                request, 
                'catalog/canvas_detail.html', 
                {'user': logged_in_user},
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

    # can't add ideas if the canvas is unavailable or if the blank canvas is being edited to by an authenticated user
    if (not user_permission(logged_in_user, canvas) and (canvas.title != 'blank' and logged_in_user.is_authenticated)):
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

    # can't remove ideas if the canvas is unavailable or if the blank canvas is being edited by an authenticated user
    if (not user_permission(logged_in_user, canvas) and (canvas.title != 'blank' and logged_in_user.is_authenticated)):
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
    canvas = idea.canvas

    if (not user_permission(logged_in_user, canvas) or (canvas.title == 'blank')):
        return HttpResponse('Unauthorized', status = 401)

    input_text = strip_tags(input_text)

    idea.text = input_text
    idea.save()

    return_idea = serialize(
        'json', 
        [idea], 
        cls=IdeaEncoder
    )

    return return_idea



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

    if (not user_permission(logged_in_user, canvas) or (canvas.title == 'blank')):
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

    if (not user_permission(logged_in_user, canvas) or (canvas.title == 'blank')):
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

    # data = pack_comments_for_json(request, canvas)
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
    
    if (not admin_permission(logged_in_user, canvas)) or (canvas.title == 'blank'):
        return HttpResponse('Forbidden', status = 403)
  
    category = comment.idea.category
    comment.delete()

    return category


# TODO: ADMIN PERMISSION REQUIRED
def comment_resolve(logged_in_user, idea_pk):
    '''
    Resolution of comments - delete all 
    '''
    idea = Idea.objects.get(pk = idea_pk)
    canvas = idea.canvas

    if (not admin_permission(logged_in_user, canvas)) or (canvas.title == 'blank'):
        return HttpResponse('Forbidden', status = 403)
    
    IdeaComment.objects.all().filter(idea = idea).delete()

    return idea.category
        




##################################################################################################################################
#                                               USER AND LANDING PAGE VIEWS                                                      #
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
        
def add_user(logged_in_user, canvas_pk, name):
    '''
    Function for addition of user to canvas
    '''

    canvas = Canvas.objects.get(pk=canvas_pk)

    if (not admin_permission(logged_in_user, canvas)) or (canvas.title == 'blank'):
        return HttpResponse('Unauthorized', status = 401)

    else:
        user = User.objects.get(username = name)

        if not user:
            print("No")
            reply = 'Error: ' + name + ' does not exist. Please try a different username.'
            return HttpResponse(reply, status = 500)

            if logged_in_user in canvas.users.all() or user in canvas.admins.all():
                reply = ''

            if user is logged_in_user:
                reply = 'Error: you\'re already a collaborator, you can\'t add yourself!'
            else:
                reply = 'Error: ' + name + ' is already a collaborator!'

            return HttpResponse(reply, status = 500)

        canvas.users.add(user)

        json_user = serialize(
            'json', 
            [user],
            cls = UserModelEncoder
        )
        
        return json_user

def delete_user(logged_in_user, canvas_pk, user_pk):
    '''
    Function for deleting a user from the canvas.
    '''
    canvas = Canvas.objects.get(pk = canvas_pk)

    if (not admin_permission(logged_in_user, canvas)) or (canvas.title == 'blank'):
        return HttpResponse('Forbidden', status = 403)


    user = User.objects.get(pk = user_pk)

    if user not in canvas.users.all():
        reply = 'Error: ' + name + ' is not a collaborator'
        return HttpResponse(reply, status = 500)

    admins = canvas.admins.all()

    # if there is one admin who is the logged-in user, do not allow them to 
    # delete themselves. It's implied that if there's one admin, the logged_in 
    # user is that admin, as earlier it is checked that the logged_in user
    # is in the canvas admin set
    if (len(admins) == 1 and user in admins):
        print("no")
        reply = 'Error: You are the only admin, you may not delete yourself!'
        return HttpResponse(reply, status = 500)

    victim_is_admin = "false"
    # if the user is also an admin, remove them from that field also
    if user in admins:
        victim_is_admin = "true"
        canvas.admins.remove(user)      

    canvas.users.remove(user)

    return victim_is_admin



def promote_user(logged_in_user, canvas_pk, user_pk):
    '''
    Function for promoting a user to admin status
    '''
    canvas = Canvas.objects.get(pk = canvas_pk)

    # check is admin
    if (not admin_permission(logged_in_user, canvas)) or (canvas.title == 'blank'):
        return HttpResponse('Forbidden', status = 403)

    user = User.objects.get(pk = user_pk)
    name_str = user.username
    admins = canvas.admins.all()

    # check presence in admin set
    if user in admins:
        # additionally check the user isn't trying to promote themselves
        if user is logged_in_user:
            name_str = 'you are'
        else: 
            name_str = name_str + ' is '
        reply = 'Error: ' + name_str + ' already an admin!'
        
        return HttpResponse(reply, status = 500)

    canvas.admins.add(user)

    json_user = serialize(
        'json', 
        [user],
        cls = UserModelEncoder
    )
    
    return json_user


def demote_user(logged_in_user, canvas_pk, user_pk):
    '''
    Function to delete a user from the admin field - this is for demotion only.
    For complete deletion, call delete user
    '''
    canvas = Canvas.objects.get(pk = canvas_pk)

    if (not admin_permission(logged_in_user, canvas)) or (canvas.title == 'blank'):
        return HttpResponse('Forbidden', status = 403)

    user = User.objects.get(pk = user_pk)
    admins = canvas.admins.all()
    # Can't delete a non-existent admin
    if user not in admins:
        reply = 'Error: ' + name + ' is not an admin'
        return HttpResponse(reply, status = 500)

    # if there is one admin who is the logged-in user, do not allow them to 
    # delete themselves
    if len(admins) == 1:
        reply = 'Error: You are the only admin, you may not demote yourself!'
        return HttpResponse(reply, status = 500)

    canvas.admins.remove(user)





##################################################################################################################################
#                                                           TAG VIEWS                                                            #
##################################################################################################################################

def add_tag(canvas_pk, logged_in_user, label):
    '''
    ADDITION OF NEW TAG 
    '''
    canvas = Canvas.objects.get(pk=canvas_pk)
    
    if (not user_permission(logged_in_user, canvas) or (canvas.title == 'blank')):
        return HttpResponse('Forbidden', status = 403)

    # check presence of tag - avoid duplicating tags
    if CanvasTag.objects.filter(label=label).exists():
        tag = CanvasTag.objects.get(label=label)

    else:
        # only create tag if it doesn't exist anywhere visible to the user
        tag = CanvasTag(label=label)

    # check tags in current canvas
    labels = canvas.tags.filter(label=label)

    if not labels:
        tag.save()
        canvas.tags.add(tag)

        json_tag = serialize(
            'json', 
            [tag], 
            cls = CanvasTagEncoder
        )
        data = get_canvasses_accessible_by_user(logged_in_user)

        return_data = {
            'public': data['public'],
            'private': data['my_private'],
            'allCanvasses': data['all_canvasses'],
            'tag': json_tag,
        }

        return return_data
    else :
        return HttpResponse("Tag already exists!", status = 302)
 

def remove_tag(tag_pk, canvas_pk):
    '''
    REMOVAL OF TAG
    '''
    canvas = Canvas.objects.get(pk=canvas_pk)
    tag = CanvasTag.objects.get(pk=tag_pk)
    canvas.tags.remove(tag)

    # delete any tags that aren't attached to a canvas: they are never useful
    CanvasTag.objects.filter(canvas_set=None).delete()

    return 


##################################################################################################################################
#                                                   MISCELLANEOUS FUNCTIONS                                                      #
################################################################################################################################## 



def get_canvasses_accessible_by_user(logged_in_user):
    '''
    function to get every canvas accessible to the currently logged-in user
    '''
    filter_kwargs = {'is_public': True}
    user_filter_kwargs = {'users': logged_in_user}
    admin_filter_kwargs = {'admins': logged_in_user}

    canvasses = Canvas.objects.all()

    # public canvasses are those where public is true
    public = canvasses.filter(**filter_kwargs)
    # private canvasses where the user is either the owner or a collaborator on the canvas
    private = canvasses.exclude(**filter_kwargs)

    my_private = (
        private.filter(**admin_filter_kwargs) | private.filter(**user_filter_kwargs)
    ).distinct()

    all_canvasses = (
        canvasses.filter(**filter_kwargs) | private.filter(**admin_filter_kwargs) | private.filter(**user_filter_kwargs)
    ).distinct()

    json_public = serialize(
        'json', 
        public,
        cls=CanvasEncoder
    )

    json_private = serialize(
        'json', 
        my_private,
        cls=CanvasEncoder
    )

    json_all_canvasses = serialize(
        'json', 
        all_canvasses,
        cls=CanvasEncoder
    )   

    data = {
        'public': json_public,
        'my_private': json_private,
        'all_canvasses': json_all_canvasses
    }

    return data

def update_canvas_session_variables(self, logged_in_user):
    data = get_canvasses_accessible_by_user(logged_in_user)

    self.request.session['public'] = data['public']
    self.request.session['private'] = data['my_private']
    self.request.session['all_canvasses'] = data['all_canvasses']

    # NOTE END: BAND-AID FOR UPDATING SESSION DATA ON LOAD

def user_permission(logged_in_user, canvas):
    return (logged_in_user in canvas.users.all() or canvas.is_public == True)

def admin_permission(logged_in_user, canvas):
    return (logged_in_user in canvas.admins.all())

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

class UserModelEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, CanvasTag):
            return str(obj)
        return super().default(obj)

    class Meta:
        model = User
        exclude = ('password',)

