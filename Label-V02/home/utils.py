
# home/utils.py
from lxml import etree
import html
import re
import os
import csv
import logging
import shutil
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from django.conf import settings  # Import Django settings

# Setup logger
logger = logging.getLogger('home')

def handle_annotation_to_csv(channels=None, full_file_path=None, selected_channel=None, annotation_data=None, task_to_do=''):
    """
    Adds an annotation row to a CSV file, creating the file and necessary directories if they don't exist.
    
    Parameters:
    - full_file_path (str): Full file path of the XML file.
    - channels (list): List of all channels available in the XML file.
    - selected_channel (str): The channel selected for the annotation.
    - annotation_data (dict): The data to be added to the CSV file. Should contain 'Start Index', 'End Index', 'Label', and 'Color'.
    - task_to_do (str): 
            The task to perform: 
                    'add' for addind data to the working CSV file, 
                    'retrieve' for retrieving existing values from the working CSV file, 
                    'save' for saving the working CSV file,
                    'remove' for removing data from the working CSV file, 
                    'reset' for resetting the working CSV file.

    Returns:
    - list: A list of dictionaries containing the existing values for the selected channel, including the newly added element.
    """

    working_csv_file_path, saving_csv_file_path = creating_file_paths(full_file_path)

    if task_to_do == 'add':
        logger.info(f"Adding data to a CSV file...\n")
        add_annotation_to_csv(channels, working_csv_file_path, selected_channel, annotation_data)
    elif task_to_do == 'retrieve':
        logger.info(f"Retrieving existing annotations from CSV file...\n")
        existing_values = retrieve_existing_annotations(working_csv_file_path, selected_channel)
        return existing_values
    elif task_to_do == 'save':
        logger.info(f"Saving the CSV file...\n")
        message, status = save_annotations_to_csv(working_csv_file_path, saving_csv_file_path)
        return message, status
    elif task_to_do == 'reset':
        logger.info(f"Resetting the working CSV file...\n")
        refresh_working_file(working_csv_file_path)
        return []
    else:
        message = f"Specify a valid task_to_do.\n"
        logger.info(message)
        return []

def creating_file_paths(full_file_path):
    """
    Creates file paths for the working and saving CSV files, creating necessary directories if they don't exist.

    Parameters:
    - channels (list): List of all channels available in the XML file.
    - full_file_path (str): Full file path of the XML file.
    - selected_channel (str): The channel selected for the annotation.
    - annotation_data (dict): The data to be added to the CSV file. Should contain 'Start Index', 'End Index', 'Label', and 'Color'.

    Returns:
    - tuple: A tuple containing the paths for the working CSV file and the saving CSV file.
    """
    try:
        # Base path from settings
        base_path = Path(settings.BASE_FILE_PATH)
        # Ensure 'CSV_Annotations' directory exists
        annotations_dir = base_path / 'CSV_Annotations'
        annotations_dir.mkdir(parents=True, exist_ok=True)
        
        # Derive relative path and the subdirectory of the xml file
        relative_path = Path(full_file_path).relative_to(base_path).with_suffix('.csv')
        subdirectory = relative_path.parent

        # Create 'Working_Folder' within the subdirectory
        working_csv_file_path = annotations_dir / subdirectory / 'Working_Folder' / relative_path.name
        working_csv_file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"working_csv_file_path = {working_csv_file_path}\n")

        # Create 'Saving_Folder' within the subdirectory
        saving_csv_file_path = annotations_dir / subdirectory / 'Saving_Folder' / relative_path.name
        saving_csv_file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"saving_csv_file_path = {saving_csv_file_path}\n")

        return working_csv_file_path, saving_csv_file_path
    except Exception as e:
        logger.error(f"Error in handle_annotation_to_csv / creating_file_paths: \n\t{str(e)}\n")

def add_annotation_to_csv(channels, working_csv_file_path, selected_channel, annotation_data):
    """
    Adds an annotation row to a CSV file, creating the file and necessary directories if they don't exist.

    Parameters:
    - channels (list): List of all channels available in the XML file.
    - working_csv_file_path (str): Full file path of the working CSV file.
    - selected_channel (str): The channel selected for the annotation.
    - annotation_data (dict): The data to be added to the CSV file. Should contain 'Start Index', 'End Index', 'Label', and 'Color'.
    """
    try:
        # Create temporary file for manipulation 
        temp_file_path = Path(working_csv_file_path).with_suffix('.tmp')
        with open(temp_file_path, mode='w', newline='') as temp_file:
            pass  # This ensures the file is truncated (emptied) if it exists
        
        # Initialize item number
        item_number = 1

        # Create and write to the CSV file
        if not working_csv_file_path.exists():
            with open(working_csv_file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                # Write header row (single row)
                header_row = []
                for channel in channels:
                    header_row.extend([f'{channel} Items', f'{channel} Start Index', f'{channel} End Index', f'{channel} Label', f'{channel} Color'])
                writer.writerow(header_row)

        # Open the working CSV file in read mode and the temporary file in write mode
        with open(working_csv_file_path, mode='r', newline='') as csv_file, open(temp_file_path, mode='w', newline='') as temp_file:
            reader = csv.reader(csv_file)
            writer = csv.writer(temp_file)

            headers = next(reader)  # Read the header row
            writer.writerow(headers)  # Write the header to the temporary file
            item_col_index = headers.index(f'{selected_channel} Items')

            row_found = False

            # Iterate through the non-empty rows after the headers row
            for row in reader:
                if not row_found and all(not row[headers.index(f'{selected_channel} {suffix}')] for suffix in ['Items', 'Start Index', 'End Index', 'Label', 'Color']):
                    # Update only the columns related to the selected channel
                    row[item_col_index] = item_number
                    row[item_col_index + 1] = annotation_data.get('Start Index', '')
                    row[item_col_index + 2] = annotation_data.get('End Index', '')
                    row[item_col_index + 3] = annotation_data.get('Label', '')
                    row[item_col_index + 4] = annotation_data.get('Color', '#d604a2')
                    row_found = True # Mark that we've found and updated the row
                else:
                    if row[item_col_index]:
                        item_number = int(row[item_col_index]) + 1
                writer.writerow(row)
            logger.info(f"Current item_number being added: {item_number}\n")

            # If no row was updated (because it was already occupied or there were no data rows), append a new row
            if not row_found:
                row_data = [''] * len(headers)
                row_data[item_col_index] = item_number
                row_data[item_col_index + 1] = annotation_data.get('Start Index', '')
                row_data[item_col_index + 2] = annotation_data.get('End Index', '')
                row_data[item_col_index + 3] = annotation_data.get('Label', '')
                row_data[item_col_index + 4] = annotation_data.get('Color', '#d604a2')
                writer.writerow(row_data)

        # Replace the working csv file with the temporary file. This will delete the temporary file.
        os.replace(temp_file_path, working_csv_file_path)
        logger.info(f"working CSV file was updated, and the temporary file was removed..\n")

    except Exception as e:
        logger.error(f"Error in handle_annotation_to_csv / add_annotation_to_csv: \n\t{str(e)}\n")

def retrieve_existing_annotations(working_csv_file_path, selected_channel):
    """
    Retrieves existing annotations for the selected channel from a CSV file.

    Parameters:
    - working_csv_file_path (str): Full file path of the working CSV file.
    - selected_channel (str): The channel selected for the annotation.

    Returns:
    - list: A list of dictionaries containing the existing values for the selected channel.
    """
    try:
        # List to store existing values
        existing_values = []

        if working_csv_file_path.exists():
            with open(working_csv_file_path, mode='r', newline='') as csv_file:
                reader = csv.reader(csv_file)
                headers = next(reader)  # Read the header row
                item_col_index = headers.index(f'{selected_channel} Items')

                # Iterate through the non-empty rows after the headers row
                for row in reader:
                    if row[item_col_index]:
                        existing_values.append({
                            'Item Number': row[item_col_index],
                            'Start Index': row[item_col_index + 1],
                            'End Index': row[item_col_index + 2],
                            'Label': row[item_col_index + 3],
                            'Color': row[item_col_index + 4],
                        })
        logger.info(f"Retrieved existing annotations for {selected_channel} from {working_csv_file_path}\n")
        return existing_values
    except Exception as e:
        logger.error(f"Error in handle_annotation_to_csv / retrieve_existing_annotations: \n\t{str(e)}\n")
        return []

def save_annotations_to_csv(working_csv_file_path, saving_csv_file_path):
    """
    Saves the working CSV file to the saving directory.

    Parameters:
    - working_csv_file_path (str): Full file path of the working CSV file.
    - saving_csv_file_path (str): Full file path where the CSV file should be saved.
    """
    try:
        # Copy the working CSV file to the saving directory
        if working_csv_file_path.exists():
            shutil.copy2(working_csv_file_path, saving_csv_file_path)
            logger.info(f"CSV file saved \n\tfrom {working_csv_file_path} \n\tto {saving_csv_file_path}\n")
            message = 'Progress Saved successfully!'
            status = True
            return message, status
        else:
            logger.error(f"Working CSV file does not exist: {working_csv_file_path}\n")
            message = 'There is no work to Save!'
            status = False
            return message, status
    except Exception as e:
        message = f"Error in handle_annotation_to_csv / save_annotations_to_csv: \n\t{str(e)}!\n"
        status = False
        logger.error(message)
        return message, status

def refresh_working_file(working_csv_file_path):
    """
    Refreshes the working CSV file by erasing its content except the headers.

    Parameters:
    - working_csv_file_path (str): Path to the working CSV file.
    """
    try:
        with open(working_csv_file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # Read the headers

        with open(working_csv_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)  # Write the headers back to the file
        
        logger.info(f"Working CSV file refreshed: \n\t{working_csv_file_path}\n")
    except Exception as e:
        logger.error(f"Error in handle_annotation_to_csv / refresh_working_file: \n\t{str(e)}\n")

def process_xml_data(file_path): # Working with WebSocket 
    file_path = html.unescape(file_path)  # Decode HTML entities
    file_path = convert_path(file_path)
    try:

        logger.info("process_xml_data function returns: ")
        severity = extract_severity(file_path)
        logger.info(f"\nASGI Extracted severity: {severity}\n")

        channels = extract_channels(file_path)
        logger.info(f"ASGI Extracted channels: {channels}\n")

        statements = extract_interpretation_statements(file_path)
        logger.info(f"ASGI Extracted statements: {statements}\n")

        return {'severity': severity, 'channels': channels, 'statements': statements}
    except Exception as e:
        logger.info(f"Error processing XML file: {e}")
        return {'error': str(e)}

def extract_severity(xml_file_path):
    unique_severity = set([
        'OTHERWISE NORMAL ECG', 'ABNORMAL ECG', 'NORMAL ECG', 
        'BORDERLINE ECG', 'DEFECTIVE ECG', 'atypical ECG', 'abnormal rhythm ECG'
    ])
    try:
        tree = etree.parse(xml_file_path)
        root = tree.getroot()
        # First try: Iterate over all elements under <Interpretation> for a match
        for elem in root.findall('.//Interpretation//*'):
            if elem.text and any(sev.lower() in elem.text.lower() for sev in unique_severity):
                return clean_text(elem.text.strip()).upper() 
        # If no match found under <Interpretation>, extend search to the entire XML file
        for elem in root.iter():
            if elem.text and any(sev.lower() in elem.text.lower() for sev in unique_severity):
                return clean_text(elem.text.strip()).upper() 
        return "" # Return empty string if no severity found in the entire document
    except Exception as e:
        logger.info(f"Error processing file {xml_file_path}: {e}")
        return ""

def clean_text(text):
    cleaned_text = re.sub(r'^\W+|\W+$', '', text)
    return cleaned_text

# Function to convert file path to a normalized path
def convert_path(path):
    return os.path.normpath(path)

def extract_channels(file_path):
    channels = []
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        for channel in root.findall('.//Channel'):
            channels.append(channel.text)
    except etree.ParseError as e:
        logger.info(f"XML parsing error: {e}")  # Print parsing errors
        raise
    return channels

def extract_interpretation_statements(xml_file_path):
    """
    Extracts statements from the Interpretation section of the XML file, excluding those 
    whose left or right statement text (case-insensitively) matches any entry in the unique_severity set.
    """
    unique_severity = set([
        'OTHERWISE NORMAL ECG', 'ABNORMAL ECG', 'NORMAL ECG', 
        'BORDERLINE ECG', 'DEFECTIVE ECG', 'atypical ECG', 'abnormal rhythm ECG'
    ])
    try:
        tree = etree.parse(xml_file_path)
        root = tree.getroot()
        interpretation = root.find('.//Interpretation')
        if interpretation is not None:
            # Pre-process unique_severity for case-insensitive comparison
            lower_unique_severity = {item.lower() for item in unique_severity}
            filtered_statements = []
            for statement in interpretation.findall('.//Statement'):
                left_text = statement.find('Leftstatement').text or ""
                right_text = statement.find('Rightstatement').text or ""
                # Filter out statements if either side matches unique_severity
                if not any(clean_text(sev.lower()) in lower_unique_severity for sev in [left_text, right_text]):                    
                    # Construct the string based on the presence of left and right statements
                    if left_text and right_text:
                        statement_str = f"{left_text}: {right_text}" 
                    elif left_text: 
                        statement_str = left_text 
                    else:
                        statement_str = right_text 
                    # Only add to filtered_statements if there's something to add
                    if statement_str:
                        filtered_statements.append(statement_str) # filtered_statements.append(statement_str.upper())

                    # filtered_statements.append({'Leftstatement': left_text, 'Rightstatement': right_text})

            return filtered_statements
        return []
    except Exception as e:
        logger.info(f"\nError processing file {xml_file_path}: {e}\n")
        return []
