# Custom Labeling Tool (Ongoing project)

A custom Django-Plotly-Dash based labeling tool used for ECG waveforms.

## Prerequisites

Before you run the WebApp, there are a few things you need to do. Follow the steps below:

### 1. Set BASE_FILE_PATH in settings.py

Go to `settings.py` in the main app (`label_V02` folder within the `Label_V02` project folder), and insert the directory path as indicated below:

```python
BASE_FILE_PATH = os.getenv('BASE_FILE_PATH', r"INSERT THE PATH OF THE ROOT DIRECTORY WHERE YOU PLACED 'Testing_Folder_Filtered' ('Testing_Folder_Filtered' should not be included in the path and the path must not end with / or #)")
```

2. Create and Activate a Virtual Environment
In the project folder (Label_V02 folder, 'Label' with capital L), create a new virtual environment. Then, cd into the project folder and activate the virtual environment. You can use pipenv as shown below:
pipenv install -r requirements.txt

