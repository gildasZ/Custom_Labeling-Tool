
# Create your views here.

# home/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import logout
from django.conf import settings
import logging

# Setup logger
logger = logging.getLogger('home')

# Existing view
def home(request):
    return redirect('login')  # Redirect to the welcome view

def custom_login(request):
    auth_logout(request)
    request.session.flush()
    return auth_views.LoginView.as_view(template_name='home/login.html')(request)

@login_required
def welcome(request):
    # Pass the base file path to the template
    context = {'base_file_path': settings.BASE_FILE_PATH}
    logger.info("The welcome function ran successfully.\t\t\t\t, and welcome.html is running!\n")
    return render(request, 'home/welcome.html', context)

# Registration view
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = UserCreationForm()
    return render(request, 'home/register.html', {'form': form})

# custom_logout view, this is the view called when I click on the logout button.
def custom_logout(request):
    auth_logout(request)
    request.session.flush()
    return render(request, 'home/logout.html')  # Render the logout page after logging out
