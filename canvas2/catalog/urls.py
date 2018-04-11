from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
  path('', views.index, name='index'),
  path('canvas-list/', views.CanvasList.as_view(), name='canvas-list'),
  path('canvas/<int:pk>/', views.CanvasDetailView.as_view(), name='canvas-detail'),
  path('delete_user/', views.delete_user, name='delete-user'),
  path('collaborators/<int:pk>', views.collaborators, name='collaborators'),
  path('idea_detail/<int:pk>/', views.idea_detail, name='idea-detail'),
  path('register/', views.register, name='register'),
  path('new_canvas/', views.new_canvas, name='new-canvas'),
  path('new_idea/', views.new_idea, name='new-idea'),
  path('comment_thread/<int:pk>', views.comment_thread, name='comment-thread'),
  path('comment_resolve/<int:pk>', views.comment_resolve, name='comment-resolve'),
  path('delete_idea/<int:pk>/', views.delete_idea, name='delete-idea'),
  path('delete_comment/<int:pk>/', views.delete_comment, name='delete-comment'),
  path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html')),
  path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html')),

]