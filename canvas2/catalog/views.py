from django.shortcuts import render, redirect
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .models import Canvas, IdeaCategory, CanvasTag, Idea, Comment
from .forms import SignUpForm

# TODO: update views based on models

# TODO: use django.utils.timezone instead of datetime
import django.utils.timezone 

@login_required
def new_canvas(request):
    canvas = Canvas(title = "New Canvas", public = False)
    canvas.save()
    
    canvas.admins.add(request.user)
    canvas.users.add(request.user)
    canvas.save()

    return redirect(canvas.get_absolute_url()) # bring user to the canvas page for the newly created canvas


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


class CanvasList(LoginRequiredMixin, generic.ListView):
    # TODO: update this based on changes in Model
    model = Canvas

    def get_context_data(self, **kwargs):
        '''
        This function's purpose is to separate the public from the private canvasses
        '''
        me = self.request.user
        context = super().get_context_data(**kwargs)

        filter_kwargs = {'public': True}
#        me_filter_kwargs = {'users': me}

        canvasses = Canvas.objects.all()

        # public canvasses are those where public is true
        public = canvasses.filter(**filter_kwargs)
        # private canvasses where the user is either the owner or a collaborator on the canvas
        private = canvasses.exclude(**filter_kwargs).filter(users__pk = me)

        context['public_canvas_list'] = public
        context['private_canvas_list'] = private

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


