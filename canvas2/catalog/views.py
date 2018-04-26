from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize
from django.utils.html import strip_tags

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
    canvas.title = 'New Canvas ' + str(canvas.pk)   

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

        context['public_canvas_list'] = public
        context['private_canvas_list'] = my_private

        return context



class CanvasDetailView(LoginRequiredMixin, generic.DetailView):
    model = Canvas

    def get_context_data(self, **kwargs):
        '''
        This function is to return a set of ideas where their canvasID attribute matches the current canvas id. 
        '''
        context = super().get_context_data(**kwargs)
        contextCID = (context['canvas'].pk)
        filter_kwargs = {'canvas': contextCID}

        ideas = Idea.objects.all()
        filtered_ideas = ideas.filter(**filter_kwargs)
        context['idea_list'] = filtered_ideas

        return context


    def post(self, request, **kwargs):
        '''
        function for post requests, sent by a canvas on loading
        purpose is to return the canvas information as a JSON
        '''
        if request.is_ajax():
            canvas_pk = request.POST['canvas_pk']
            canvas = Canvas.objects.get(pk = canvas_pk)


            users = canvas.users.all()
            admins = canvas.admins.all()

            ideas = Idea.objects.all().filter(canvas = canvas)
            comments = IdeaComment.objects.all().filter(idea__in=ideas)
            
            tags = canvas.tags.all()
            
            # only serialise ideas if they exist
            json_ideas = serialize(
                'json', 
                ideas, 
                cls=IdeaEncoder
            )
            json_comments = serialize(
                'json', 
                comments, 
                cls=IdeaCommentEncoder
            )
            json_tags = serialize(
                'json', 
                tags, 
                cls=CanvasTagEncoder
            )

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

            data = {
                'ideas': json_ideas,
                'comments': json_comments,
                'tags': json_tags,
                'users': json_users,
                'admins': json_admins
            }

            return JsonResponse(data, safe = False)




##################################################################################################################################
#                                                         IDEA VIEWS                                                             #
################################################################################################################################## 



# TODO: USER PERMISSION REQUIRED
# TODO: AJAX POST CANVAS PK
def new_idea(request):
    '''
    Creation of a new idea. This gets the id for the canvas in which it is created from the calling URL
    '''
    if request.method == 'POST':
        logged_in_user = request.user
        # available_canvasses = Canvas.objects.filter(users__pk = logged_in_user.pk)
        canvas_pk = request.POST['canvas_pk']
        category = request.POST['category']
        canvas = Canvas.objects.get(pk = canvas_pk)

        if logged_in_user in canvas.users.all():
            idea = Idea(
                canvas = canvas, 
                category = category, 
                text = ''
            )
            idea.save()
            # This is so I can click on it in the django admin - should probably delete later
            idea.title = 'Canvas ' + str(canvas_pk) +  ' Idea ' + str(idea.pk)
            idea.save()

            return_idea = serialize(
                'json', 
                [idea], 
                cls=IdeaEncoder
            )
            return JsonResponse(return_idea, safe = False)            

        else:
            return HttpResponse('Unauthorized', status = 401)



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

        if logged_in_user in canvas.users.all():
            return_idea = serialize(
                'json', 
                [idea], 
                cls=IdeaEncoder
            )
            idea.delete()
            print("gone")
            # print(Idea.objects.get(pk = idea_pk))
            return JsonResponse(return_idea, safe = False);
        else:
            print("No")
            return HttpResponse('Unauthorized', status = 401)




# TODO: USER PERMISSION REQUIRED
@login_required
def idea_detail(request):
    
    if request.method == 'POST':
        idea_pk = request.POST['idea_pk']
        new_text = request.POST['input_text']
        new_text = strip_tags(new_text)

        idea_inst = get_object_or_404(Idea, pk = idea_pk)
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

    if logged_in_user in canvas.users.all():


        if request.method == 'POST':
            comments = IdeaComment.objects.all().filter(idea = idea)
            
            json_comments = serialize(
                'json', 
                comments, 
                cls = IdeaCommentEncoder
            )
            return JsonResponse(json_comments, safe = False)

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

        if logged_in_user in canvas.users.all():
            comment = IdeaComment(
                user = logged_in_user, 
                author_name = logged_in_user.username,
                text = text,
                idea = idea
            )
            comment.save()
            json_comments = serialize(
                'json', 
                [comment], 
                cls = IdeaCommentEncoder
            )
            return JsonResponse(json_comments, safe = False)
        else:
            return HttpResponse('Unauthorized', status = 401)


# TODO: ADMIN PERMISSION REQUIRED
def comment_resolve(request):
    '''
    Resolution of comments - delete all 
    '''

    idea_pk = request.POST['idea_pk']
    idea = Idea.objects.get(pk = pk)

    IdeaComment.objects.all().filter(idea = idea).delete()
    return JsonResponse('', safe = False)



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
            return JsonResponse('', safe = False)
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



# TODO: ADMIN PERMISSION REQUIRED
def collaborators(request, pk):
    '''
    Page for viewing the collaborators of a canvas
    '''
    canvas = Canvas.objects.get(pk = pk)
    admins = canvas.admins.all()
    users = canvas.users.all()

    if request.method == 'POST':
        form = AddUserForm(request.POST)

        if form.is_valid():
            new_user = User.objects.get(username = (form.cleaned_data['name']))
            
            if new_user not in admins and new_user not in users :
                canvas.users.add(new_user)
                
                return redirect(request.META.get('HTTP_REFERER'))

            else:
                print('User already a collaborator')

    else:
        form = AddUserForm(initial = {
            'name': ''
        })


    return render(
        request, 
        'catalog/collaborators.html',
        {
            'admins': admins,
            'users': users,
            'canvas': canvas, 
            'form': form 
        }
    )



#TODO: Do not allow a user to delete themself if they're the only admin - the only way that should be possible is by deleting the canvas itself
def delete_admin(request, user_pk, canvas_pk):
    '''
    Function for deleting an admin
    '''

    return redirect(request.META.get('HTTP_REFERER'))




# TODO: ADMIN PERMISSION REQUIRED
def delete_user(request, user_pk, canvas_pk):
    '''
    Function for deleting a user 
    '''
    canvas = Canvas.objects.get(pk = canvas_pk)
    user = User.objects.get(pk = user_pk)
    logged_in_user = request.user

    canvas.users.remove(user)


    return redirect(request.META.get('HTTP_REFERER'))





##################################################################################################################################
#                                                   MISCELLANEOUS FUNCTIONS                                                      #
################################################################################################################################## 





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



class UserModelEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, CanvasTag):
            return str(obj)
        return super().default(obj)

    class Meta:
        model = User
        exclude = ('password',)

