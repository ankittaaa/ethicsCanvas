from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


from .models import Canvas, IdeaCategory, CanvasTag, Idea, IdeaComment
from .forms import SignUpForm, IdeaForm, CommentForm, AddUserForm


# TODO: Create permissions for actions (add/remove users, delete canvas...)
import django.utils.timezone 




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

    if user == canvas.owner:
        canvas.delete()
    else:
        return HttpResponse('Unauthorized', status = 401)

    return redirect(request.META.get('HTTP_REFERER'))



# TODO: USER PERMISSION REQUIRED
# TODO: AJAX POST CANVAS PK
def new_idea(request):
    '''
    Creation of a new idea. This gets the id for the canvas in which it is created from the calling URL
    '''
    ref = request.META.get('HTTP_REFERER')
    # carve the referer by '/' to isolate the canvas pk that exists in the url
    split_ref = ref.split('/')  
    split_len = len(split_ref)
    # the pk is the second-last element, the last element is whitespace following the last '/' character at the end of the url 
    canvas_pk = split_ref[split_len - 2]
    canvas = Canvas.objects.get(pk = canvas_pk)
    logged_in_user = request.user
    # available_canvasses = Canvas.objects.filter(users__pk = logged_in_user.pk)
    


    if logged_in_user in canvas.users.all():
        idea = Idea(canvas = canvas)
        idea.save()
        idea.title = canvas.title + ', Idea ' + str(idea.pk)
        idea.save()
    else:
        return HttpResponse('Unauthorized', status = 401)


    # initialise the new idea with the canvas instance that called it 
    # TODO: any other initial fields necessary?
    
    # print(split_ref[split_len - 2])
    return redirect(idea.get_absolute_url())



def comment_thread(request, pk):
    '''
    View function for displaying the comment thread of an idea, and for posting a new comment
    '''
    idea = Idea.objects.get(pk = pk)


    if request.method == 'POST':
        form = CommentForm(request.POST)

        if form.is_valid():
            text = form.cleaned_data['text']

            comment = IdeaComment.objects.create(text = text, idea = idea, user = request.user)
            return redirect(request.META.get('HTTP_REFERER'))

    else:
        form = CommentForm(initial = { 
            'text': ''
        })


    comment_list = IdeaComment.objects.all().filter(idea = idea)


    return render(
        request, 
        'catalog/comment_thread.html', 
        {'comments': comment_list,
         'idea': idea,
        'form': form}
    )

# TODO: ADMIN PERMISSION REQUIRED
def comment_resolve(request, pk):
    '''
    Resolution of comments - delete all 
    '''
    print(':D')
    idea = Idea.objects.get(pk = pk)
    print(idea)
    IdeaComment.objects.all().filter(idea = idea).delete()
    return redirect(request.META.get('HTTP_REFERER'))


# TODO: USER PERMISSION REQUIRED (author of idea || admin? )
def delete_idea(request, pk):
    '''
    Deletion of an idea - return to the calling page
    '''
    Idea.objects.get(pk = pk).delete()
    return redirect(request.META.get('HTTP_REFERER'))


# TODO: ADMIN PERMISSION REQUIRED
def delete_comment(request, pk):
    '''
    Deletion of an idea - return to the calling page
    '''
    IdeaComment.objects.get(pk = pk).delete()
    return redirect(request.META.get('HTTP_REFERER'))



def index(request):
    return render(request, 'index.html')



def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
              username = form.cleaned_data['name']
              email = form.cleaned_data['email']
              password = form.cleaned_data['password']

              newUser = User.objects.create_user(username = username, email = email, password = password)

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


# TODO: USER PERMISSION REQUIRED
def idea_detail(request, pk):

    idea_inst = get_object_or_404(Idea, pk=pk)
    
    if request.method == 'POST':
        form = IdeaForm(request.POST)

        if form.is_valid():
            idea_inst.text = form.cleaned_data['text']
            idea_inst.save()
            return redirect(idea_inst.canvas.get_absolute_url())
        else:
            print('INVALID')
    else:
        form = IdeaForm(initial = {
            'text': idea_inst.text,
        })
    
    return render(
        request,
        'catalog/idea_detail.html', 
        {'form': form, 'idea': idea_inst}
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
        {'admins': admins,
        'users': users,
        'canvas': canvas, 
        'form': form }
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

        my_private = private.filter(**admin_filter_kwargs)
        my_private = my_private | private.filter(**user_filter_kwargs)

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



