from dotenv import load_dotenv
import os

load_dotenv()



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

