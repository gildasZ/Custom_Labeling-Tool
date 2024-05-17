
# home/utils.py
from lxml import etree
import html
import re
import os
import csv
from pathlib import Path
from django.conf import settings  # Import Django settings


def add_annotation_to_csv(full_file_path, channels, selected_channel, annotation_data):
    """
    Adds an annotation row to a CSV file, creating the file and necessary directories if they don't exist.
    
    Parameters:
    - full_file_path (str): Full file path of the XML file.
    - channels (list): List of all channels available in the XML file.
    - selected_channel (str): The channel selected for the annotation.
    - annotation_data (dict): The data to be added to the CSV file. Should contain 'Start Index', 'End Index', 'Label', and 'Color'.
    
    Returns:
    - int: The item number for the added row.
    """
    # Base path from settings
    base_path = Path(settings.BASE_FILE_PATH)
    # Ensure 'CSV_Annotations' directory exists
    annotations_dir = base_path / 'CSV_Annotations'
    annotations_dir.mkdir(parents=True, exist_ok=True)
    
    # Derive relative path and create corresponding directories
    relative_path = Path(full_file_path).relative_to(base_path).with_suffix('.csv')
    print(f"\n\nrelative_path = {relative_path}\n\n") #######################################
    csv_file_path = annotations_dir / relative_path
    print(f"\n\ncsv_file_path = {csv_file_path}\n\n") #######################################
    csv_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize item number
    item_number = 1

    # Create and write to the CSV file
    if not csv_file_path.exists():
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write header row (single row)
            header_row = []
            for channel in channels:
                header_row.extend([f'{channel} Items', f'{channel} Start Index', f'{channel} End Index', f'{channel} Label', f'{channel} Color'])
            writer.writerow(header_row)

    else:
        # If the file exists, determine the next item number
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.reader(file)
            headers = next(reader)  # Read header row
            item_col_index = headers.index(f'{selected_channel} Items')
            for row in reader: # Iterate over data rows, the header row was already skipped by next(reader)
                if row[item_col_index]:
                    item_number = int(row[item_col_index]) + 1

    # Prepare the row to add
    row_data = [''] * len(headers) ###############################################
    start_index = annotation_data.get('Start Index', '')
    end_index = annotation_data.get('End Index', '')
    label = annotation_data.get('Label', '')
    color = annotation_data.get('Color', '')
    
    channel_start_index = headers.index(f'{selected_channel} Items')
    row_data[channel_start_index] = item_number
    row_data[channel_start_index + 1] = start_index
    row_data[channel_start_index + 2] = end_index
    row_data[channel_start_index + 3] = label
    row_data[channel_start_index + 4] = color

    # Append the row to the CSV file
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row_data)
    
    return item_number


def process_xml_data(file_path): # Working with WebSocket 
    file_path = html.unescape(file_path)  # Decode HTML entities
    file_path = convert_path(file_path)
    try:

        print("process_xml_data function returns: ")
        severity = extract_severity(file_path)
        print("\nASGI Extracted severity:", severity, "\n")

        channels = extract_channels(file_path)
        print("ASGI Extracted channels:", channels, "\n")

        statements = extract_interpretation_statements(file_path)
        print("ASGI Extracted statements:", statements, "\n")

        return {'severity': severity, 'channels': channels, 'statements': statements}
    except Exception as e:
        print("Error processing XML file:", e)
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
        print(f"Error processing file {xml_file_path}: {e}")
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
        print("XML parsing error:", e)  # Print parsing errors
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
        print(f"\nError processing file {xml_file_path}: {e}\n")
        return []
