from flask import Flask, request, jsonify, g
import asyncio
from main_scratch import main, last_api_response
import json
import threading
from screen_recording import *
from multiprocessing import Process, Value

app = Flask(__name__)

@app.route('/computer_usage/', methods=['POST'])
async def run_main():
    global recording
    try:
        recording_flag = Value('b', True)
        data = request.json
        if data and 'instruction' in data:
            import sys
            sys.argv = ["main_scratch.py", data['instruction']]

        ##starting the screen recording as a sub-process
        screen_process = Process(target=record_screen, kwargs={
            "output_file": "screen_recording.avi",
            "recording_flag": recording_flag
        })
        screen_process.start()

        await main(g)
        recording_flag.value = False  
        screen_process.join(timeout=5)


        if screen_process.is_alive():
            screen_process.terminate()
            print("Screen recording process forcefully terminated.")

        if hasattr(g, "last_api_response") and g.last_api_response:
            with open("last_api_response.json", "w") as json_file:
                json.dump(g.last_api_response, json_file, indent=4)
            return jsonify({"status": "success", "api_response": g.last_api_response}), 200
        else:
            return jsonify({"status": "error", "message": "No API response recorded."}), 500
    except Exception as e:
        recording = False
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
