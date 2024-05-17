"# Custom_Labeling-Tool" 

A custom Django-Plotly-Dash based labeling tool used for ECG waveforms 

You will have to go into settings.py in the main app ('label_V02' folder that is in 'Label_V02' project folder), and insert the directory path as indicated here:

BASE_FILE_PATH = os.getenv('BASE_FILE_PATH', r" INSERT THE PATH OF THE ROOT DIRECTORY WHERE YOUR PLACED 'Testing_Folder_Filtered' ('Testing_Folder_Filtered' Should not be included in the path and the path must not end with / or \) ")
