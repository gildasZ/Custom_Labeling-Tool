
import os
from lxml import etree
from pathlib import Path
import re
import html

def main():
    delete_filtered_files()
    root_dir = Path('.')
    for xml_file in root_dir.rglob('*.xml'):
        process_and_filter_xml(xml_file)

def delete_filtered_files():
    root_dir = Path('.')
    for filtered_file in root_dir.rglob('*_filtered.xml'):
        try:
            os.remove(filtered_file)
            print(f"Deleted file: {filtered_file}")
        except Exception as e:
            print(f"Error deleting file {filtered_file}: {e}")

def process_and_filter_xml(file_path):
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()

        # Extract required information
        severity = extract_severity(root)
        statements = extract_interpretation_statements(root)
        channels_data = extract_channels_with_data(root)

        # Create a new root for the filtered XML
        new_root = etree.Element("FilteredData")

        if severity:
            severity_element = etree.SubElement(new_root, "Severity")
            severity_element.text = severity

        # if statements:
        #     statements_element = etree.SubElement(new_root, "Statements")
        #     for statement in statements:
        #         statement_element = etree.SubElement(statements_element, "Statement")
        #         statement_element.text = statement
                
        if statements:
            interpretation_element = etree.SubElement(new_root, "Interpretation")
            for statement in statements:
                statement_element = etree.SubElement(interpretation_element, "Statement")
                left_statement_element = etree.SubElement(statement_element, "Leftstatement")
                left_statement_element.text = statement.get('Leftstatement', "")
                right_statement_element = etree.SubElement(statement_element, "Rightstatement")
                right_statement_element.text = statement.get('Rightstatement', "")

        if channels_data:
            channels_element = etree.SubElement(new_root, "ChannelsData")
            for record_data in channels_data:
                channels_element.append(record_data)

        # Save the filtered XML to a new file
        filtered_file_path = file_path.with_name(f"{file_path.stem}_filtered.xml")
        etree.ElementTree(new_root).write(filtered_file_path, pretty_print=True, encoding='UTF-8')
        print(f"Filtered XML saved to: {filtered_file_path}")

    except Exception as e:
        print(f"Error processing XML file {file_path}: {e}")

def extract_severity(root):
    unique_severity = set([
        'OTHERWISE NORMAL ECG', 'ABNORMAL ECG', 'NORMAL ECG', 
        'BORDERLINE ECG', 'DEFECTIVE ECG', 'atypical ECG', 'abnormal rhythm ECG'
    ])
    try:
        for elem in root.findall('.//Interpretation//*'):
            if elem.text and any(sev.lower() in elem.text.lower() for sev in unique_severity):
                return clean_text(elem.text.strip()).upper()
        for elem in root.iter():
            if elem.text and any(sev.lower() in elem.text.lower() for sev in unique_severity):
                return clean_text(elem.text.strip()).upper()
        return "" 
    except Exception as e:
        print(f"Error extracting severity: {e}")
        return ""

def clean_text(text):
    cleaned_text = re.sub(r'^\W+|\W+$', '', text)
    return cleaned_text

def extract_channels_with_data(root):
    channels_data = []
    try:
        for record_data in root.findall('.//RecordData'):
            # Clone the RecordData element and all its children
            channels_data.append(record_data)
    except etree.ParseError as e:
        print(f"XML parsing error: {e}")
    return channels_data

def extract_interpretation_statements(root):
    unique_severity = set([
        'OTHERWISE NORMAL ECG', 'ABNORMAL ECG', 'NORMAL ECG', 
        'BORDERLINE ECG', 'DEFECTIVE ECG', 'atypical ECG', 'abnormal rhythm ECG'
    ])
    try:
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


                    # if left_text and right_text:
                    #     statement_str = f"{left_text}: {right_text}" 
                    # elif left_text: 
                    #     statement_str = left_text 
                    # else:
                    #     statement_str = right_text 


                    statement_str = {'Leftstatement': left_text,
                                     'Rightstatement': right_text}

                    # Only add to filtered_statements if there's something to add
                    if statement_str:
                        filtered_statements.append(statement_str) # filtered_statements.append(statement_str.upper())

                    # filtered_statements.append({'Leftstatement': left_text, 'Rightstatement': right_text})

            return filtered_statements
        return []
    except Exception as e:
        print(f"\nError extracting statements: {e}\n")
        return []

if __name__ == "__main__":
    main()
