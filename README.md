# Custom_Labeling-Tool

## Description
This ongoing project is a custom labeling tool based on Django-Plotly-Dash, specifically designed for labeling ECG waveforms. It allows users to annotate ECG waveforms easily through a web-based interface.

## Installation

### Prerequisites
Before running the WebApp, you need to set up your environment:

1. **Setting the Base File Path:**
   - Navigate to `settings.py` in the `label_V02` folder within the `Label_V02` project directory.
   - Update the `BASE_FILE_PATH` variable with the root directory path where you've placed the `Testing_Folder_Filtered`. Make sure this path does not include 'Testing_Folder_Filtered' itself and does not end with a `/` or `\`.

    ```python
    BASE_FILE_PATH = os.getenv('BASE_FILE_PATH', r"INSERT YOUR PATH HERE")
    ```

2. **Virtual Environment:**
   - Create a new virtual environment in the `Label_V02` project folder.
   - Activate the virtual environment. If you're using pipenv, the commands are:
     ```bash
     cd Label_V02  # Navigate into the project folder
     pipenv shell  # Activate the virtual environment
     ```

3. **Dependencies:**
   - Install the required packages from `requirements.txt` using pipenv:
     ```bash
     pipenv install -r requirements.txt
     ```

## Running the Application

To run the application, execute the following command:

```bash
python manage.py runserver
 ```

You will see the following line in the terminal, indicating the server is running:

```bash
Starting ASGI/Daphne version 4.1.2 development server at http://127.0.0.1:8000/
 ```

