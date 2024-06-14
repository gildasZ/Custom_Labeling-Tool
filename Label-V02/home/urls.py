
# home/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import home, register, custom_logout, custom_login, welcome
from home.dash_apps.finished_apps import display_ecg_graph

urlpatterns = [
    path('', home, name='home'),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'), # Handles the behavior on clicking the logout button.    
    path('register/', register, name='register'),
    path('welcome/', welcome, name='welcome'),  # Add this line
]
