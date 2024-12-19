import cv2
import numpy as np
import mss
import time
from multiprocessing import Process, Value
import subprocess



# def record_screen(output_file="myvideo.mp4", fps=15, recording_flag=None):
#     with mss.mss() as sct:
#         monitor = sct.monitors[1]  
#         width = monitor["width"]
#         height = monitor["height"]
#         #fourcc = cv2.VideoWriter_fourcc(*"XVID")
#         fourcc = cv2.VideoWriter_fourcc(*"mp4v")
#         out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

#         print("Starting screen recording...")
#         while recording_flag.value: 
#             frame = np.array(sct.grab(monitor))
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

#             out.write(frame)
#             time.sleep(1 / fps)

#         print("Stopping screen recording...")
#         out.release()




def record_screen(output_file="screen_recording.mp4", fps=15, recording_flag=None):
    # Define the screen capture area (first monitor)
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        width = monitor["width"]
        height = monitor["height"]


        aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        aws_session_token = os.environ.get("AWS_SESSION_TOKEN")
        aws_region = os.environ.get("AWS_REGION")
        
        # GStreamer command for streaming to Kinesis        
        gst_command = (
            f"gst-launch-1.0 -v appsrc ! videoconvert ! video/x-raw,format=I420,width={width},height={height},framerate={fps}/1 ! "
            f"x264enc speed-preset=ultrafast tune=zerolatency ! video/x-h264,stream-format=avc,alignment=au ! "
            f"kvssink stream-name=stream3 storage-size=512 "
            f"log-config=/home/saur/amazon-kinesis-video-streams-producer-sdk-cpp/kvs_log_configuration "
            f"access-key={aws_access_key} secret-key={aws_secret_key} session-token={aws_session_token} "
            f"aws-region={aws_region}"
        )

        gst_process = subprocess.Popen(gst_command, shell=True, stdin=subprocess.PIPE)

        # Set up OpenCV for screen recording
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

        print("Starting screen recording and streaming...")

        while recording_flag.value:
            # Capture screen frame
            frame = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # Convert BGRA to BGR
            resized_frame = cv2.resize(frame, (width, height))  # Resize frame
            
            # Write frame to file
            out.write(resized_frame)

            # Send frame to GStreamer for streaming
            if gst_process:
                gst_process.stdin.write(resized_frame.tobytes())

            time.sleep(1 / fps)

        print("Stopping screen recording and streaming...")
        
        # Close the OpenCV video writer
        out.release()
        
        # Terminate the GStreamer process
        gst_process.terminate()



