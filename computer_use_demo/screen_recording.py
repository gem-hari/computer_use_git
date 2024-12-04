import cv2
import numpy as np
import mss
import time
from multiprocessing import Process, Value

def record_screen(output_file="screen_recording.avi", fps=15, recording_flag=None):
    with mss.mss() as sct:
        monitor = sct.monitors[1]  
        width = monitor["width"]
        height = monitor["height"]
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

        print("Starting screen recording...")
        while recording_flag.value: 
            frame = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            out.write(frame)
            time.sleep(1 / fps)

        print("Stopping screen recording...")
        out.release()
