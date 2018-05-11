from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize
from django.utils.html import strip_tags
from django.db.models import Q
from django.contrib.sessions.backends.base import SessionBase

from .models import Canvas, CanvasTag, Idea, IdeaComment
from .forms import SignUpForm, IdeaForm, CommentForm, AddUserForm


# TODO: Create permissions for actions (add/remove users, delete canvas...)
import django.utils.timezone 





##################################################################################################################################
#                                                           CANVAS VIEWS                                                         #
##################################################################################################################################

 

@login_required
def new_canvas(request):
    creator = request.user

    canvas = Canvas(is_public = False, owner = creator)
    canvas.save()
    canvas.title = f'New Canvas {canvas.pk}'   

    canvas.admins.add(creator)
    canvas.users.add(creator)
    canvas.save()

    return redirect(canvas.get_absolute_url()) # bring user to the canvas page for the newly created canvas



def delete_canvas(request, pk):
    '''
    Function for deleting a canvas
    '''
    user = request.user
    canvas = Canvas.objects.get(pk = pk)

    if user in canvas.admins.all():
        canvas.delete()
    else:
        return HttpResponse('Forbidden', status = 403)

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

        if logged_in_user in canvas.users.all() or logged_in_user in canvas.admins.all() or canvas.is_public == True:
            if request.is_ajax():
                op = request.GET['operation']

                if op == 'add_tag':
                    '''
                    ADDITION OF NEW TAG 
                    '''
                    label = request.GET['tag']
                    
                    # check presence of tag - avoid duplicating tags
                    tag = CanvasTag.objects.get(label=label)

                    if (tag == None):
                        # only create tag if it doesn't exist anywhere visible to the user
                        tag = CanvasTag(label = request.GET['tag'])

                    # check tags in current canvas
                    labels = canvas.tags.filter(label = label)

                    if not labels:
                        tag.save()
                        canvas.tags.add(tag)

                        json_tags = serialize(
                            'json', 
                            canvas.tags.all(), 
                            cls = CanvasTagEncoder
                        )
                        update_canvas_session_variables(self, logged_in_user)

                        public_canvasses = request.session['public']
                        private_canvasses = request.session['private']
                        all_canvasses = request.session['all_canvasses']

                        data = {
                            'tags': json_tags,
                            'public': public_canvasses,
                            'private': private_canvasses,
                            'allCanvasses': all_canvasses
                        }

                        return JsonResponse(data, safe = False)
                    else :
                        return HttpResponse("Tag already exists!", status = 500)

                

                # NOTE: for now, deleting a tag only deletes from the current canvas
                # it may still be useful in other canvasses if it exists there
                elif op == 'delete_tag':
                    '''
                    REMOVAL OF TAG
                    '''
                    tag = CanvasTag.objects.get(pk=request.GET['tag_pk'])
                    canvas.tags.remove(tag)

                    # delete any tags that aren't attached to a canvas: they are never useful
                    CanvasTag.objects.filter(canvas_set=None).delete()


                    return JsonResponse(request.GET['tag_pk'], safe=False)





                else:
                    '''
                    THE ELSE STANDS IN PLACE FOR INITIALISE OPERATION
                    '''
                    update_canvas_session_variables(self, logged_in_user)

                    users = canvas.users.all()
                    admins = canvas.admins.all()
                    tags = canvas.tags.all()

                    ideas = Idea.objects.filter(canvas = canvas)
                    comments = IdeaComment.objects.filter(idea__in=ideas)
                    
                    # NOTE: Removed comments, users and admins. These are all
                    # serialised and sent to browser in different views
                    json_users = '""'
                    json_admins = '""'
                    json_comments = '""'
                    json_ideas = '""'
                    json_tags = '""'
                    
                    # these already exist in JSON form
                    public_canvasses = request.session['public']
                    private_canvasses = request.session['private']
                    all_canvasses = request.session['all_canvasses']

                    if ideas:
                    # only serialise ideas if they exist
                        json_ideas = serialize(
                            'json', 
                            ideas, 
                            cls = IdeaEncoder
                        )

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


                    data = {
                        'ideas': json_ideas,
                        'comments': json_comments,
                        'tags': json_tags,
                        'admins': json_admins,
                        'users': json_users,
                        'public': public_canvasses,
                        'private': private_canvasses,
                        'allCanvasses': all_canvasses
                    }

                    return JsonResponse(data, safe = False)
            else:
                return render(
                    request, 
                    'catalog/canvas_detail.html', 
                ) 
        else:
            return HttpResponse('Unauthorized', status = 401)








    

     





##################################################################################################################################
#                                                         IDEA VIEWS                                                             #
################################################################################################################################## 



# TODO: USER PERMISSION REQUIRED
def new_idea(request):
    '''
    Creation of a new idea. This gets the id for the canvas in which it is created from the calling URL
    '''
    if request.method == 'POST':
        logged_in_user = request.user
        # available_canvasses = Canvas.objects.filter(users__pk = logged_in_user.pk)
        canvas_pk = request.POST['canvas_pk']
        category = request.POST['category']

        try:
            canvas = Canvas.objects.get(pk = canvas_pk)
        except Canvas.DoesNotExist:
            return error

        # can't add ideas if the canvas is unavailable
        if logged_in_user not in canvas.users.all() and canvas.is_public == False:
            return HttpResponse('Unauthorized', status = 401)
            
        idea = Idea(
            canvas = canvas, 
            category = category, 
            text = ''
        )
        idea.save()
        # This is so I can click on it in the django admin - should probably delete later
        idea.title = f'Canvas {canvas.pk} Idea {idea.pk}'
        idea.save()

        return_idea = serialize(
            'json', 
            [idea], 
            cls=IdeaEncoder
        )
        # TODO: why is the JSON not safe?
        # NOTE: without safe = False, throws the following:
        # 'TypeError: In order to allow non-dict objects to be serialized set the safe parameter to False.'
        return JsonResponse(return_idea, safe = False)            



# ADMIN PERMISSION REQUIRED FOR NOW
def delete_idea(request):
    '''
    Deletion of an idea - return to the calling page
    '''
    if request.POST:
        idea_pk = request.POST['idea_pk']
        idea = Idea.objects.get(pk = idea_pk)
        canvas = idea.canvas
        logged_in_user = request.user

        if logged_in_user in canvas.users.all() or canvas.is_public == True:
            idea.delete()
            return JsonResponse('""', safe = False);
        else:
            return HttpResponse('Unauthorized', status = 401)




# TODO: USER PERMISSION REQUIRED
def idea_detail(request):
    if request.method == 'POST':
        logged_in_user = request.user
        idea_pk = request.POST['idea_pk']
        idea_inst = get_object_or_404(Idea, pk = idea_pk)
        canvas = idea_inst.canvas

        if logged_in_user in canvas.users.all() or canvas.is_public == True:

            new_text = request.POST['input_text']
            new_text = strip_tags(new_text)

            idea_inst.text = new_text
            idea_inst.save()

            return_idea = serialize(
                'json', 
                [idea_inst], 
                cls=IdeaEncoder
            )

            return JsonResponse(return_idea, safe = False)

        else:
            return HttpResponse('Unauthorized', status = 401)





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

    if logged_in_user in canvas.users.all() or canvas.is_public == True:
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

        else:
            return render(
                request, 
                'catalog/comment_thread.html', 
            )
    else:
        return HttpResponse('Unauthorized', status = 401)


def new_comment(request):
    if request.method == 'POST':
        text = request.POST['input_text']
        text = strip_tags(text)
        
        idea_pk = request.POST['idea_pk']
        idea = Idea.objects.get(pk = idea_pk)
        
        canvas = idea.canvas
        logged_in_user = request.user

        if logged_in_user in canvas.users.all() or canvas.is_public == True:
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
                'author': comment.user.username
            }

            return JsonResponse(data, safe = False)
        else:
            return HttpResponse('Unauthorized', status = 401)


# TODO: ADMIN PERMISSION REQUIRED
def comment_resolve(request):
    '''
    Resolution of comments - delete all 
    '''
    if request.method == 'POST':
        logged_in_user = request.user

        idea_pk = request.POST['idea_pk']
        idea = Idea.objects.get(pk = pk)
        canvas = idea.canvas

        if logged_in_user in canvas.admins.all():
            IdeaComment.objects.all().filter(idea = idea).delete()
            return JsonResponse('""', safe = False)
        else:
            return HttpResponse('Forbidden', status = 403)


# TODO: ADMIN PERMISSION REQUIRED
def delete_comment(request):
    '''
    Deletion of an idea - return to the calling page
    '''
    if request.method == 'POST':
        logged_in_user = request.user
        comment_pk = request.POST['comment_pk']
        
        comment = IdeaComment.objects.get(pk = comment_pk)
        canvas = comment.idea.canvas
        
        if logged_in_user in canvas.admins.all():
            comment.delete()
            return JsonResponse('""', safe = False)
        else :
            return HttpResponse('Forbidden', status = 403)






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



def collaborators(request, pk):
    '''
    Page for viewing the collaborators of a canvas
    '''
    canvas = Canvas.objects.get(pk = pk)

    logged_in_user = request.user

    # check user is an admin
    if logged_in_user in canvas.admins.all():
        if request.is_ajax():
            if request.method == 'GET':
                admins = canvas.admins.all()
                users = canvas.users.all()

                json_users = serialize(
                    'json', 
                    users, 
                    cls=UserModelEncoder
                )
                json_admins = serialize(
                    'json', 
                    admins, 
                    cls=UserModelEncoder
                )

                json_me = serialize(
                    'json',
                    [logged_in_user],
                    cls=UserModelEncoder

                )

                data = {
                    'users': json_users,
                    'admins': json_admins,
                    'me': json_me,
                    'canvasPK': pk
                }

                return JsonResponse(data, safe = False)

            # 
            # HANDLES ADD-USER FUNCTIONALITY
            # 
            elif request.method == 'POST':
                name = request.POST['name']
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
                data = {
                    'user': json_user
                }
                
                return JsonResponse(data, safe = False)

        else:
            return render(
                request, 
                'catalog/collaborators.html', 
            )
    else:
        return HttpResponse('Unauthorized', status = 401)


def add_admin(request):

    if request.method == 'POST':
        canvas_pk = request.POST['canvas_pk']
        canvas = Canvas.objects.get(pk = canvas_pk)
        logged_in_user = request.user

        # check is admin
        if logged_in_user not in canvas.admins.all():
            return HttpResponse('Forbidden', status = 403)

        user_pk = request.POST['user_pk']
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
            cls=UserModelEncoder

        )

        data = {
            'user': json_user
        }

        return JsonResponse(data, safe = False)



def delete_admin(request):
    '''
    Function to delete a user from the admin field - this is for demotion only.
    For complete deletion, call delete user
    '''
    print("KILL")
    
    if request.method == 'POST':
        canvas_pk = request.POST['canvas_pk']
        canvas = Canvas.objects.get(pk = canvas_pk)
        logged_in_user = request.user

        if logged_in_user not in canvas.admins.all():
            return HttpResponse('Forbidden', status = 403)

        user_pk = request.POST['user_pk']
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
        reply = 'Admin privileges revoked for ' + user.username
        return JsonResponse(reply, safe = False)


def delete_user(request):
    '''
    Function for deleting a user entirely from the canvas.
    '''
    if request.method == 'POST':
        canvas_pk = request.POST['canvas_pk']
        canvas = Canvas.objects.get(pk = canvas_pk)
        logged_in_user = request.user

        if logged_in_user not in canvas.admins.all():
            return HttpResponse('Forbidden', status = 403)

        user_pk = request.POST['user_pk']
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

        canvas.users.remove(user)

        # if the user is also an admin, remove them from that field also
        if user in admins:
            canvas.admins.remove(user)
            reply = user.username + ' removed from users and admins.'
            return JsonResponse(reply, safe = False)

        # if the user isn't an admin as well, only say they're gone from users
        reply = user.username + ' removed from users.'
        return JsonResponse(reply, safe = False)




##################################################################################################################################
#                                                           TAG VIEWS                                                            #
##################################################################################################################################

 







##################################################################################################################################
#                                                   MISCELLANEOUS FUNCTIONS                                                      #
################################################################################################################################## 

def update_canvas_session_variables(self, logged_in_user):
     # NOTE BEGIN: BAND-AID FOR UPDATING SESSION DATA ON LOAD

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

    self.request.session['public'] = json_public
    self.request.session['private'] = json_private
    self.request.session['all_canvasses'] = json_all_canvasses

    # NOTE END: BAND-AID FOR UPDATING SESSION DATA ON LOAD



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

