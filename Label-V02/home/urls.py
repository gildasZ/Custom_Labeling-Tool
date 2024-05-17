
# home/urls.py
from django.urls import path
from .views import home
from home.dash_apps.finished_apps import display_ecg_graph

urlpatterns = [
    path('', home, name = 'home'),
]
