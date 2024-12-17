from dotenv import load_dotenv
import os

load_dotenv()

def check_folder_exists(folder_path):
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        print(f"Folder '{folder_path}' exists.")
        return True
    else:
        print(f"Folder '{folder_path}' does not exist.")
        return False


def check_file_exists(file_path):
    if os.path.exists(file_path) and os.path.isfile(file_path):
        print(f"File '{file_path}' exists.")
        return True
    else:
        print(f"File '{file_path}' does not exist.")
        return False


def clear_files_in_folder(folder_path):
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        print(f"Folder '{folder_path}' exists. Clearing files...")
        
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)            
            if os.path.isfile(item_path):
                try:
                    os.remove(item_path)
                    print(f"Deleted file: {item_path}")
                except Exception as e:
                    print(f"Failed to delete {item_path}. Reason: {e}")
        print(f"All files in '{folder_path}' have been removed.")
    else:
        print(f"Folder '{folder_path}' does not exist.")

#clear_files_in_folder(os.getenv("OUTPUT_DIR"))