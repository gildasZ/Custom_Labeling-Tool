"# Custom_Labeling-Tool"  (Ongoing project)

A custom Django-Plotly-Dash based labeling tool used for ECG waveforms 

There are few things to do before you run the WebApp. I will describe them below, as well as how to run the app:

1. Insert the appropriate BASE_FILE_PATH in settings.py:
   
You will have to go into settings.py in the main app ('label_V02' folder that is in 'Label_V02' project folder), and insert the directory path as indicated here:

BASE_FILE_PATH = os.getenv('BASE_FILE_PATH', r" INSERT THE PATH OF THE ROOT DIRECTORY WHERE YOUR PLACED 'Testing_Folder_Filtered' ('Testing_Folder_Filtered' Should not be included in the path and the path must not end with / or '\') ")

3. Create a new virtual environment in the project folder ('Label_V02' folder, 'Label' with capital L),
   then 'cd' into the project folder,
   and activate the virtual environment (I used pipenv).
   
4. Then install the requirements.txt with the command (if you used pipenv to create your virtual environment):
   pipenv install -r requirements.txt

5. Next, run the command:
   python manage.py runserver

6. You will see this line in the terminal:
   Starting ASGI/Daphne version 4.1.2 development server at http://127.0.0.1:8000/

7. Copy the link or click on it to open it in your browser.

8. To use the WebApp:
   -Click on: Select your directory!
   -Then select the 'Testing_Folder_Filtered' directory that is provided in the repository.
   -Next, click on the dropdown on the right of 'Choose a Lead: ' and choose any lead.
   -Then the waveform corresponding to the lead will appear.
   -Next for the annotations, you will will click on the waveform at a given location once, then click somewhere else the second time.
   -An input field will appear for you to type in the 'Annotation' (what you want to call that segement of the graph).
   -Then click on 'Submit' or 'Press Enter' and the annotation information will appear at the bottom of the waveform.
