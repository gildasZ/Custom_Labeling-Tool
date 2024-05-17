import os
from pathlib import Path


def main():
    # delete_filtered_files()
    delete_original_files()


def delete_original_files():
    root_dir = Path('.')
    for xml_file in root_dir.rglob('*.xml'):
        if not xml_file.name.endswith('_filtered.xml'):
            try:
                os.remove(xml_file)
                print(f"Deleted original file: {xml_file}")
            except Exception as e:
                print(f"Error deleting file {xml_file}: {e}")


def delete_filtered_files():
    root_dir = Path('.')
    for filtered_file in root_dir.rglob('*_filtered.xml'):
        try:
            os.remove(filtered_file)
            print(f"Deleted file: {filtered_file}")
        except Exception as e:
            print(f"Error deleting file {filtered_file}: {e}")

    for filtered_file in root_dir.rglob('*_filtered_filtered.xml'):
        try:
            os.remove(filtered_file)
            print(f"Deleted file: {filtered_file}")
        except Exception as e:
            print(f"Error deleting file {filtered_file}: {e}")


if __name__ == "__main__":
    main()
