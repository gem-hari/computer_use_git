import cv2
import numpy as np
import mss
import time
from multiprocessing import Process, Value

def record_screen(output_file="screen_recording.mp4", fps=15, recording_flag=None):
    with mss.mss() as sct:
        monitor = sct.monitors[1]  
        width = monitor["width"]
        height = monitor["height"]
        #fourcc = cv2.VideoWriter_fourcc(*"XVID")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

        print("Starting screen recording...")
        while recording_flag.value: 
            frame = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            out.write(frame)
            time.sleep(1 / fps)

        print("Stopping screen recording...")
        out.release()



import mss
import numpy as np
import cv2
import time
import subprocess

def record_screen_to_kinesis(stream_name, aws_region, access_key, secret_key, fps=15, recording_flag=None):
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Select primary monitor
        width = monitor["width"]
        height = monitor["height"]

        # Create a GStreamer pipeline
        gst_command = (
            f"gst-launch-1.0 -v appsrc ! videoconvert ! video/x-raw,format=I420,width={width},height={height},framerate={fps}/1 ! "
            f"x264enc speed-preset=ultrafast tune=zerolatency ! video/x-h264,stream-format=avc,alignment=au ! "
            f"kvssink stream-name={stream_name} storage-size=512 "
            f"access-key={access_key} secret-key={secret_key} aws-region={aws_region}"
        )

        # Start GStreamer process
        gst_process = subprocess.Popen(gst_command, shell=True, stdin=subprocess.PIPE)

        print("Starting screen recording to Kinesis Video Stream...")
        try:
            while recording_flag.value:
                frame = np.array(sct.grab(monitor))  # Capture screen frame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # Convert BGRA to BGR
                resized_frame = cv2.resize(frame, (width, height))  # Resize frame
                gst_process.stdin.write(resized_frame.tobytes())  # Send frame to GStreamer
                time.sleep(1 / fps)
        except Exception as e:
            print(f"Error during screen recording: {e}")
        finally:
            recording_flag.value = False
            gst_process.stdin.close()
            gst_process.wait()
            print("Screen recording to Kinesis stopped.")
