from flask import Flask, request, jsonify, g
import asyncio
from main_scratch import main, last_api_response
import json
import threading
from threading import Lock
from screen_recording import *
from multiprocessing import Process, Value
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from s3 import upload_to_s3,extract_file_from_s3
from datetime import datetime

app = Flask(__name__)

api_lock = Lock()
is_running = False

@app.route('/computer_usage/', methods=['POST'])
async def run_main():
    global recording
    global is_running
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
            sys.argv = ["main_scratch.py", data['instruction']]
        else:
            return jsonify({"status": "error", "message": "No Instruction found in the request."}), 500

        process_start_time = datetime.now()
        process_start_time = process_start_time.strftime("%Y%m%d_%H%M%S")


        video_record_name = "screen_recording_"+process_start_time + "_.mp4"
        
        ##starting the screen recording as a sub-process
        screen_process = Process(target=record_screen, kwargs={
            "output_file": video_record_name,
            "recording_flag": recording_flag
        })
        screen_process.start()

        await main(g)
        recording_flag.value = False  
        screen_process.join(timeout=5)


        if screen_process.is_alive():
            screen_process.terminate()
            print("Screen recording process forcefully terminated.")
        
        object_name=None
        object_name = upload_to_s3(s3_client,video_record_name, bucket)
        print("File uploaded to s3 with the name ,", object_name)

        is_running = False
        if api_lock.locked():
            api_lock.release()


        if hasattr(g, "last_api_response") and g.last_api_response:
            with open("last_api_response.json", "w") as json_file:
                json.dump(g.last_api_response, json_file, indent=4)
            return jsonify({"status": "success", "api_response": g.last_api_response,"video_record_s3_bucket":bucket,"video_response_s3_object_name":object_name}), 200
        else:
            return jsonify({"status": "error", "message": "No API response recorded."}), 500
    except Exception as e:
        recording_flag.value = False  
        screen_process.join(timeout=5)
        is_running = False
        if api_lock.locked():
            api_lock.release()
        if screen_process.is_alive():
            screen_process.terminate()
            print("Screen recording process forcefully terminated.")
        return jsonify({"status": "error", "message": str(e)}), 500        

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
