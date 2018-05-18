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

    if not admin_permission(logged_in_user, canvas):
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

        if not user_permission(logged_in_user, canvas):
            return HttpResponse('Unauthorized', status = 401)
        if request.is_ajax():
            op = request.GET['operation']

            if op == 'add_tag':
                '''
                ADDITION OF NEW TAG 
                '''
                label = request.GET['tag']
                
                # check presence of tag - avoid duplicating tags
                if CanvasTag.objects.filter(label=label).exists():
                    tag = CanvasTag.objects.get(label=label)

                else:
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

                json_self=serialize(
                    'json',
                    [logged_in_user],
                    cls=UserModelEncoder
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
            ) 




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
        if not user_permission(logged_in_user, canvas):
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
        ideas = Idea.objects.filter(category=category)

        # get the comments for the idea in the category updated
        category_comments = IdeaComment.objects.filter(idea__in=ideas)
        # and the entire comments list for good measure

        # send all ideas for the category - this is so they're always in database order
        return_idea = serialize(
            'json', 
            [idea], 
            cls=IdeaEncoder
        )

        data = {
            'idea': return_idea,
            # 'categoryComments': return_category_comments,
        }

        # TODO: why is the JSON not safe?
        # NOTE: without safe = False, throws the following:
        # 'TypeError: In order to allow non-dict objects to be serialized set the safe parameter to False.'
        return JsonResponse(data, safe = False)            



def delete_idea(request):
    '''
    Deletion of an idea - return to the calling page
    '''
    if request.POST:
        idea_pk = request.POST['idea_pk']
        idea = Idea.objects.get(pk = idea_pk)
        canvas = idea.canvas
        logged_in_user = request.user

        if not user_permission(logged_in_user, canvas):
            return HttpResponse('Unauthorized', status = 401)

        category = idea.category
        idea.delete()

        data = {
            'i': request.POST['i'],
            'category': category
        }

        return JsonResponse(data, safe = False)  



# TODO: USER PERMISSION REQUIRED
def idea_detail(request):
    if request.method == 'POST':
        logged_in_user = request.user
        idea_pk = request.POST['idea_pk']
        idea_inst = get_object_or_404(Idea, pk = idea_pk)
        canvas = idea_inst.canvas

        if not user_permission(logged_in_user, canvas):
            return HttpResponse('Unauthorized', status = 401)

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

    if not user_permission(logged_in_user, canvas):
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


def new_comment(request):
    if request.method == 'POST':
        text = request.POST['input_text']
        text = strip_tags(text)
        
        idea_pk = request.POST['idea_pk']
        idea = Idea.objects.get(pk = idea_pk)
        
        canvas = idea.canvas
        logged_in_user = request.user

        if not user_permission(logged_in_user, canvas):
            return HttpResponse('Unauthorized', status = 401)

        comment = IdeaComment(
            user = logged_in_user, 
            text = text,
            idea = idea
        )
        comment.save()

        data = pack_comments_for_json(request, canvas)

        return JsonResponse(data, safe = False)


# TODO: ADMIN PERMISSION REQUIRED
def comment_resolve(request):
    '''
    Resolution of comments - delete all 
    '''
    if request.method == 'POST':
        logged_in_user = request.user

        idea_pk = request.POST['idea_pk']
        idea = Idea.objects.get(pk = idea_pk)
        canvas = idea.canvas

        if not admin_permission(logged_in_user, canvas):
            return HttpResponse('Forbidden', status = 403)
        
        else:
            IdeaComment.objects.all().filter(idea = idea).delete()
            data = {
                'category': idea.category,
                'i': request.POST['i'],
            }
            return JsonResponse(data, safe = False)
        


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
        
        if not admin_permission(logged_in_user, canvas):
            return HttpResponse('Forbidden', status = 403)
      
        else:
            comment.delete()
            data = pack_comments_for_json(request, canvas)
            return JsonResponse(data, safe = False)


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



def collaborators(request):
    '''
    Page for viewing the collaborators of a canvas

    All collaborator-modifying views will return the admins and the users, as there is a 
    general function called by the callbacks for each in the javascript file
    '''

    logged_in_user = request.user

    # check user is an admin
    if request.is_ajax():
            # HANDLES ADD-USER FUNCTIONALITY
            # 
        if request.method == 'POST':
            canvas = Canvas.objects.get(pk=request.POST['canvas_pk'])

            if not admin_permission(logged_in_user, canvas):
                return HttpResponse('Unauthorized', status = 401)

            else:
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

                json_users = serialize(
                    'json', 
                    canvas.users.all(),
                    cls = UserModelEncoder
                )

                json_admins = serialize(
                    'json', 
                    canvas.admins.all(),
                    cls = UserModelEncoder
                )

                data = {
                    'users': json_users,
                    'admins': json_admins
                }
                
                return JsonResponse(data, safe = False)

        else:
            return render(
                request, 
                'catalog/collaborators.html', 
            )
        


def promote_user(request):

    if request.method == 'POST':
        canvas_pk = request.POST['canvas_pk']
        canvas = Canvas.objects.get(pk = canvas_pk)
        logged_in_user = request.user

        # check is admin
        if not admin_permission(logged_in_user, canvas):
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

        json_users = serialize(
            'json', 
            canvas.users.all(),
            cls = UserModelEncoder
        )

        json_admins = serialize(
            'json', 
            canvas.admins.all(),
            cls = UserModelEncoder
        )

        data = {
            'users': json_users,
            'admins': json_admins
        }
        
        return JsonResponse(data, safe = False)



def demote_admin(request):
    '''
    Function to delete a user from the admin field - this is for demotion only.
    For complete deletion, call delete user
    '''
    print("KILL")
    
    if request.method == 'POST':
        canvas_pk = request.POST['canvas_pk']
        canvas = Canvas.objects.get(pk = canvas_pk)
        logged_in_user = request.user

        if not admin_permission(logged_in_user, canvas):
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

        json_users = serialize(
            'json', 
            canvas.users.all(),
            cls = UserModelEncoder
        )

        json_admins = serialize(
            'json', 
            canvas.admins.all(),
            cls = UserModelEncoder
        )

        data = {
            'users': json_users,
            'admins': json_admins
        }
        
        return JsonResponse(data, safe = False)


def delete_user(request):
    '''
    Function for deleting a user entirely from the canvas.
    '''
    if request.method == 'POST':
        canvas_pk = request.POST['canvas_pk']
        canvas = Canvas.objects.get(pk = canvas_pk)
        logged_in_user = request.user

        if not admin_permission(logged_in_user, canvas):
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

        # if the user is also an admin, remove them from that field also
        if user in admins:
            canvas.admins.remove(user)      

        canvas.users.remove(user)


        json_users = serialize(
            'json', 
            canvas.users.all(),
            cls = UserModelEncoder
        )

        json_admins = serialize(
            'json', 
            canvas.admins.all(),
            cls = UserModelEncoder
        )

        data = {
            'users': json_users,
            'admins': json_admins
        }
        
        return JsonResponse(data, safe = False)




##################################################################################################################################
#                                                           TAG VIEWS                                                            #
##################################################################################################################################

 


##################################################################################################################################
#                                                   MISCELLANEOUS FUNCTIONS                                                      #
################################################################################################################################## 

def pack_comments_for_json(request, canvas):
    '''
    Function to pack the comments for specific idea, every comment, and the current idea
    for returning to frontend in order to update the idea list component and the comment component
    '''
    idea = Idea.objects.get(pk=request.POST['idea_pk'])
            
    ideas = Idea.objects.filter(canvas = canvas)
    comments = IdeaComment.objects.filter(idea=idea)
    all_comments = IdeaComment.objects.filter(idea__in=ideas)
    
    # every comment
    json_all_comments = serialize(
        'json',
        all_comments,
        cls=IdeaCommentEncoder
    )

    # comments on modified idea
    json_comments = serialize(
        'json', 
        comments, 
        cls = IdeaCommentEncoder
    )

    # modified idea
    return_idea = serialize(
        'json', 
        [idea], 
        cls=IdeaEncoder
    )

    data = {
        'idea': return_idea,
        'comments': json_comments,
        'allComments': json_all_comments,
        # index for finding where the idea is in the array back in javascript
        'i': request.POST['i']
    }
    return data



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

