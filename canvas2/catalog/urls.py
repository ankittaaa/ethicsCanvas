from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('', views.index, name='index'),

    path('canvas/<int:pk>/', views.CanvasDetailView.as_view(), name='canvas-detail'),
    path('project-list/', views.ProjectListView.as_view(), name='project-list'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('new_canvas/<int:canvas_type>/', views.new_canvas, name='new-canvas'),
    path('delete_canvas/<int:pk>/', views.delete_canvas, name='delete-canvas'), 
    path('new_project/', views.new_project, name='new-project'),
    path('delete_project/<int:pk>/', views.delete_project, name='delete-project'), 
    path('register/', views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html')),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html')),

]