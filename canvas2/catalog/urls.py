from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('', views.index, name='index'),

    path('canvas/<int:pk>/', views.CanvasDetailView.as_view(), name='canvas-detail'),
    path('canvas-list/', views.CanvasList.as_view(), name='canvas-list'),
    # path('collaborators/', views.collaborators, name='collaborators'),

    path('new_canvas/', views.new_canvas, name='new-canvas'),
    path('delete_canvas/<int:pk>/', views.delete_canvas, name='delete-canvas'), 

    # path('new_idea/', views.new_idea, name='new-idea'),
    # path('delete_idea/', views.delete_idea, name='delete-idea'),
    # path('idea_detail/', views.idea_detail, name='idea-detail'),
    
    # path('comment_thread/<int:pk>/', views.comment_thread, name='comment-thread'),
    # path('comment_resolve/', views.comment_resolve, name='comment-resolve'),
    # path('new_comment/', views.new_comment, name='new-comment'),
    # path('delete_comment/', views.delete_comment, name='delete-comment'),
    
    # path('delete_user/', views.delete_user, name='delete-user'),
    # path('promote_user/', views.promote_user, name='promote-user'),
    # path('demote_admin/', views.demote_admin, name='demote-admin'),
    

    path('register/', views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html')),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html')),

]