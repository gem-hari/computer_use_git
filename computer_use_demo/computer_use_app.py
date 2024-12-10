from flask import Flask, request, jsonify, g
import asyncio
from main_entry import main, last_api_response
import json
import threading
from threading import Lock
from screen_recording import *
from multiprocessing import Process, Value
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from s3 import upload_to_s3,extract_file_from_s3
from datetime import datetime
from delete_tmp_files import clear_files_in_folder,check_folder_exists,check_file_exists

app = Flask(__name__)

api_lock = Lock()
is_running = False
from dotenv import load_dotenv
import os

load_dotenv()

@app.route('/computer_use/', methods=['POST'])
async def run_computer_use():
    print("Testing POC endpoint activated")
    last_api_response =None
    global recording
    global is_running
    save_dir = os.getenv("RESUTS_DIR")
    process_start_time = datetime.now()
    process_start_time = process_start_time.strftime("%Y%m%d_%H%M%S")
    video_record_name = "screen_recording_"+process_start_time + "_.mp4"
    try:
        if not api_lock.acquire(blocking=False):
            return jsonify({"status": "error", "message": "API is busy. Please try again later."}), 503
        is_running = True

        s3_client = boto3.client(service_name='s3')
        bucket = "computerusebucket"
        recording_flag = Value('b', True)
        data = request.json

        if data and 'instruction' in data:
            import sys
            sys.argv=["main_entry.py", data['instruction'],"False"]
        else:
            return jsonify({"status": "error", "message": "No Instruction found in the request."}), 500
        
        ##starting the screen recording as a sub-process
        os.makedirs(save_dir, exist_ok=True)
        screen_process = Process(target=record_screen, kwargs={
            "output_file": save_dir + video_record_name,
            "recording_flag": recording_flag
        })
        screen_process.start()

        await main(g)
        last_api_response = g.last_api_response
        recording_flag.value = False  
        screen_process.join(timeout=5)


        if screen_process.is_alive():
            screen_process.terminate()
            print("Screen recording process forcefully terminated.")
        
        object_name=None
        object_name = upload_to_s3(s3_client,save_dir+video_record_name, bucket)
        print("File uploaded to s3 with the name ,", object_name)

        ###close all the apps started 
        print("Closing all the apps on UI")
        sys.argv = ["main_entry.py", "Close all the apps like firefox, terminal running on the UI."]
        await main(g)

        print("Clearing the screenshots and locally saved recording")
        if check_folder_exists(save_dir) and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(save_dir)
        if check_folder_exists(save_dir+"screenshots/") and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(save_dir+"screenshots")
        if check_folder_exists(os.getenv("OUTPUT_DIR")) and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(os.getenv("OUTPUT_DIR"))
        
        is_running = False
        if api_lock.locked():
            api_lock.release()

        if hasattr(g, "last_api_response") and last_api_response:
            with open(save_dir+"last_api_response.json", "w") as json_file:
                json.dump(last_api_response, json_file, indent=4)
            return jsonify({"status": "success", "api_response": last_api_response,"video_record_s3_bucket":bucket,"video_response_s3_object_name":object_name}), 200
        else:
            return jsonify({"status": "error", "message": "No API response recorded."}), 500
    except Exception as e:
        recording_flag.value = False  
        is_running = False
        try:
            screen_process.join(timeout=5)
            if screen_process.is_alive():
                screen_process.terminate()
                print("Screen recording process forcefully terminated.")
        except Exception as e:
            print("Error occured while trying to stop process in exception ", e)
        object_name=None
        if check_file_exists(save_dir+video_record_name):
            object_name = upload_to_s3(s3_client,save_dir+video_record_name, bucket)
            print("File uploaded to s3 with the name ,", object_name)



        if check_folder_exists(save_dir) and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(save_dir)
        if check_folder_exists(save_dir+"screenshots/") and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(save_dir+"screenshots")
        if check_folder_exists(os.getenv("OUTPUT_DIR")) and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(os.getenv("OUTPUT_DIR"))
        if api_lock.locked():
            api_lock.release()
        if object_name is None:
            return jsonify({"status": "error", "message": str(e)}), 500        
        else:
            return jsonify({"status":"error","message":str(e),"video_record_s3_bucket":bucket,"video_response_s3_object_name":object_name}), 500

@app.route('/testing_poc/', methods=['POST'])
async def run_testing_poc():
    print("Testing POC endpoint activated")
    last_api_response =None
    global recording
    global is_running
    save_dir = os.getenv("RESUTS_DIR")
    process_start_time = datetime.now()
    process_start_time = process_start_time.strftime("%Y%m%d_%H%M%S")
    video_record_name = "screen_recording_"+process_start_time + "_.mp4"
    try:
        if not api_lock.acquire(blocking=False):
            return jsonify({"status": "error", "message": "API is busy. Please try again later."}), 503
        is_running = True

        s3_client = boto3.client(service_name='s3')
        bucket = "computerusebucket"
        recording_flag = Value('b', True)
        data = request.json
    
        if data and 'instruction' in data:
            import sys
            sys.argv=["main_entry.py", data['instruction'],"True"]
        else:
            return jsonify({"status": "error", "message": "No Instruction found in the request."}), 500
        
        ##starting the screen recording as a sub-process
        os.makedirs(save_dir, exist_ok=True)
        screen_process = Process(target=record_screen, kwargs={
            "output_file": save_dir + video_record_name,
            "recording_flag": recording_flag
        })
        screen_process.start()

        await main(g)
        last_api_response = g.last_api_response
        recording_flag.value = False  
        screen_process.join(timeout=5)

        if screen_process.is_alive():
            screen_process.terminate()
            print("Screen recording process forcefully terminated.")
        
        object_name=None
        object_name = upload_to_s3(s3_client,save_dir+video_record_name, bucket)
        print("File uploaded to s3 with the name ,", object_name)

        ###close all the apps started 
        print("Closing all the apps on UI")
        sys.argv = ["main_entry.py", "Close all the apps like firefox, terminal running on the UI."]
        await main(g)

        print("Clearing the screenshots and locally saved recording")
        if check_folder_exists(save_dir) and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(save_dir)
        if check_folder_exists(save_dir+"screenshots/") and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(save_dir+"screenshots")
        if check_folder_exists(os.getenv("OUTPUT_DIR")) and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(os.getenv("OUTPUT_DIR"))
        
        is_running = False
        if api_lock.locked():
            api_lock.release()

        if hasattr(g, "last_api_response") and last_api_response:
            with open(save_dir+"last_api_response.json", "w") as json_file:
                json.dump(last_api_response, json_file, indent=4)
            return jsonify({"status": "success", "api_response": last_api_response,"video_record_s3_bucket":bucket,"video_response_s3_object_name":object_name}), 200
        else:
            return jsonify({"status": "error", "message": "No API response recorded."}), 500
    except Exception as e:
        recording_flag.value = False  
        is_running = False
        try:
            screen_process.join(timeout=5)
            if screen_process.is_alive():
                screen_process.terminate()
                print("Screen recording process forcefully terminated.")
        except Exception as e:
            print("Error occured while trying to stop process in exception ", e)
        object_name=None
        if check_file_exists(save_dir+video_record_name):
            object_name = upload_to_s3(s3_client,save_dir+video_record_name, bucket)
            print("File uploaded to s3 with the name ,", object_name)

        if check_folder_exists(save_dir) and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(save_dir)
        if check_folder_exists(save_dir+"screenshots/") and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(save_dir+"screenshots")
        if check_folder_exists(os.getenv("OUTPUT_DIR")) and os.getenv("DELETE_TMP_FILES").lower() =="true":
            clear_files_in_folder(os.getenv("OUTPUT_DIR"))
        if api_lock.locked():
            api_lock.release()
        if object_name is None:
            return jsonify({"status": "error", "message": str(e)}), 500        
        else:
            return jsonify({"status":"error","message":str(e),"video_record_s3_bucket":bucket,"video_response_s3_object_name":object_name}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
