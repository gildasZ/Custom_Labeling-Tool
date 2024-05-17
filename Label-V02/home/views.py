
# Create your views here.

# home/views.py
from django.shortcuts import render
from django.conf import settings
import logging

# Setup logger
logger = logging.getLogger('home')

# Existing view
def home(request):
    # Pass the base file path to the template
    context = {'base_file_path': settings.BASE_FILE_PATH}
    logger.info("The home function ran successfully.\t\t\t\t, and welcome.html is running!\n")
    return render(request, 'home/welcome.html', context)
