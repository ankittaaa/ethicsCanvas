from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('', views.index, name='index'),

    # LOG-IN / SIGN-UP
    path('register/', views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html')),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html')),
    

    # PROJECT
    path('project-list/', views.ProjectListView.as_view(), name='project-list'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('new_project/', views.new_project, name='new-project'),
    path('delete_project/<int:pk>/', views.delete_project, name='delete-project'), 
    

    # CANVAS
    path('canvas/<int:pk>/', views.CanvasDetailView.as_view(), name='canvas-detail'),
    path('new_canvas/<int:canvas_type>/', views.new_canvas, name='new-canvas'),
    path('delete_canvas/<int:pk>/', views.delete_canvas, name='delete-canvas'), 


    # IDEAS
    path('new_trial_idea/', views.new_trial_idea, name='new-trial-idea'),
    path('new_idea/', views.new_idea, name='new-idea'),
    path('delete_idea/', views.delete_idea, name='delete-idea'),
    path('edit_idea/', views.edit_idea, name='edit-idea'),


    # COMMENTS
    path('new_comment/', views.new_comment, name='new-comment'),
    path('delete_comment/', views.delete_comment, name='delete-comment'),
    path('resolve_individual_comment/', views.single_comment_resolve, name='single-comment-resolve'),
    path('resolve_all_comments/', views.all_comment_resolve, name='all-comment-resolve'),


    # COLLABORATORS
    path('add_user/', views.add_user, name='add-user'),
    path('delete_user/', views.delete_user, name='delete-user'),
    path('promote_user/', views.promote_user, name='promote-user'),
    path('demote_user/', views.demote_user, name='demote-user'),
    path('toggle_public/', views.toggle_public, name='toggle-public'),

    
    # TAGS
    path('add_tag/', views.add_tag, name='add-tag'),
    path('delete_tag/', views.delete_tag, name='delete-tag'),   
]