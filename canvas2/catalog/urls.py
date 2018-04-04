from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
  path('', views.index, name='index'),
  path('canvas-list/', views.CanvasList.as_view(), name='canvas-list'),
  path('canvas/<int:pk>/', views.CanvasDetailView.as_view(), name='canvas-detail'),
  path('register/', views.register, name='register'),
  path('new_canvas/', views.new_canvas, name='new-canvas'),
  path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html')),
  path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html')),

]