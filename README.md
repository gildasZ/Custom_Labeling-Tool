# Custom_Labeling-Tool

## Description
This ongoing project is a custom labeling tool based on Django-Plotly-Dash, specifically designed for labeling ECG waveforms. It allows users to annotate ECG waveforms easily through a web-based interface.

## Installation

### Prerequisites
Before running the WebApp, you need to set up your environment:

1. **Redis Installation (Windows)**
      
      To install Redis on Windows, you can follow these steps:
      
      **Option 1: Install via MSI Executable in this repository**
      
      - Locate the Redis executable `Redis-x64-5.0.14.1.msi` from this repository.
      - Run the executable and follow the installation prompts.
      - During the installation process, check `Add the Redis installation folder to the PATH environment variable.`
      - Keep the rest as default and follow the remaining installation prompts.
      
      **Option 2: Download the Latest Release**
      
      - Visit the [Redis Releases](https://github.com/tporadowski/redis/releases) page.
      - Download the latest release or the same version.
      - Run the installer and follow the installation instructions.
      - During the installation process, check `Add the Redis installation folder to the PATH environment variable.`
      - Keep the rest as default and follow the remaining installation prompts.
      
      Once installed, ensure Redis is running properly by executing the following command in your terminal or command prompt:
      
      ```bash
      redis-server
      ```
      
      Then check if you get `PONG` when you run these following commands in your terminal or command prompt:
   
      ```bash
      redis-cli
      ping
      ```

3. **Setting the Base File Path:**
   - Navigate to `settings.py` in the `label_V02` folder within the `Label-V02` project directory.
   - Update the `BASE_FILE_PATH` variable with the root directory path where you've placed the folder `Testing_Folder_Filtered`. Make sure this path does not include 'Testing_Folder_Filtered' itself and does not end with a `/` or `\`.
  
     ```python
     BASE_FILE_PATH = os.getenv('BASE_FILE_PATH', r"INSERT YOUR PATH HERE")
     # Example
     # BASE_FILE_PATH = os.getenv('BASE_FILE_PATH', r"C:\Users\gildasZ\OneDrive\Documents\LABORATORY\Testing GitHub\Custom_Labeling-Tool")
     ```

4. **Virtual Environment:**
   - Create a new virtual environment in the `Label-V02` project folder.
   - Activate the virtual environment. If you're using pipenv, the commands are:
     ```bash
     cd Label-V02  # Navigate into the project folder
     pipenv shell  # Activate the virtual environment
     ```

5. **Dependencies:**
   - Install the required packages from `requirements.txt` using pipenv:
     ```bash
     pipenv install -r requirements.txt
     ```

6. **Database Setup:**

   You have two options for setting up the database: using PostgreSQL or the default SQLite.

   **Option 1: PostgreSQL**
   - Ensure the default database configuration in `settings.py` is commented out.
   - Create a PostgreSQL database named `db_label_v02`.
   - Update the database configuration in `settings.py` (look for the following in the file):

     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.postgresql',
             'NAME': 'db_label_v02',
             'USER': 'postgres',
             'PASSWORD': '12345',
             'HOST': 'localhost',  # It is marked as 'Server' in SQL Shell
         }

     ```

   - Run migrations to set up the database schema:
     ```bash
     python manage.py makemigrations
     python manage.py migrate
     ```
     
   - Collect static files:
     ```bash
     python manage.py collectstatic
     ```

   **Option 2: Default SQLite**
   - Ensure the PostgreSQL database configuration in `settings.py` is commented out.
   - No additional setup is required. Ensure the default database configuration in `settings.py` is uncommented (look for the following in the file):
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.sqlite3',
             'NAME': BASE_DIR / 'db.sqlite3',
         }
     }
     ```

   - Run migrations to set up the database schema:
     ```bash
     python manage.py makemigrations
     python manage.py migrate
     ```
     
   - Collect static files:
     ```bash
     python manage.py collectstatic
     ```

6. **Placement of the custom list of labels:** 

   You need to replace the custom labels file named Testing_existence.csv in the project directory, which is called Label-V02. Ensure that you follow the format of the existing file.

## Running the Application

To run the application, execute the following command:

```bash
python manage.py runserver
 ```

You will see the following line in the terminal, indicating the server is running:

```bash
Starting ASGI/Daphne version 4.1.2 development server at http://127.0.0.1:8000/
 ```


Open your web browser and navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to access the WebApp.

## Usage

### Select Your Directory:
- Click on the "Select your directory!" button.
- Choose the `Testing_Folder_Filtered` directory provided in the repository.

### Select a Lead:
- Use the dropdown menu right of "Choose a Lead:" to select any ECG lead.

### Viewing Waveforms:
- The waveform corresponding to the selected lead will be displayed.

### Adding Annotations:
- Click on the waveform where you want to start the annotation, and click again where it ends.
- An input field will appear. Type in your annotation description.
- Submit the annotation by clicking 'Submit' or pressing 'Enter'.
- Your annotation will be displayed below the waveform.

## Contributing
Feel free to fork this project and contribute by submitting a pull request. I appreciate your input!

## License
This project is licensed under the MIT License - see the LICENSE.md file for details.
