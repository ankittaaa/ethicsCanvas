from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('', views.index, name='index'),

    path('canvas/<int:pk>/', views.CanvasDetailView.as_view(), name='canvas-detail'),
    path('canvas-list/', views.CanvasList.as_view(), name='canvas-list'),
    path('idea_detail/', views.idea_detail, name='idea-detail'),
    path('collaborators/<int:pk>', views.collaborators, name='collaborators'),

    path('new_canvas/', views.new_canvas, name='new-canvas'),
    path('new_idea/', views.new_idea, name='new-idea'),

    path('comment_thread/<int:pk>', views.comment_thread, name='comment-thread'),
    path('comment_resolve/<int:pk>', views.comment_resolve, name='comment-resolve'),

    path('delete_idea/', views.delete_idea, name='delete-idea'),
    path('delete_comment/<int:pk>/', views.delete_comment, name='delete-comment'),
    path('delete_canvas/<int:pk>/', views.delete_canvas, name='delete-canvas'), 
    path('delete_user/<int:user_pk>/<int:canvas_pk>/', views.delete_user, name='delete-user'),
    path('delete_admin/<int:admin_pk>/<int:canvas_pk>/', views.delete_admin, name='delete-admin'),
    
    path('register/', views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html')),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html')),

]