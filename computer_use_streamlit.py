import streamlit as st
import requests
import json
import os 
import boto3

st.title("Computer use streamlit APP")
st.subheader("Enter an instruction to call the API")

with st.form("instruction_form"):
    instruction = st.text_input("Instruction:", "")
    task_type = st.selectbox(
    "Select Task Type:",
    ["Computer use", "Testing poc"]
    )
    submit_button = st.form_submit_button("Submit")

if submit_button:
    if task_type == "Computer use":
        api_url = "http://13.53.114.198:8001/computer_use/" 
    else:
        api_url = "http://13.53.114.198:8001/testing_poc/"

    if instruction.strip() == "":
        st.error("Please enter a valid instruction.")
    else:
        headers = {"Content-Type": "application/json"}
        payload = {"instruction": instruction}
        # "use_case": task_type}
        try:
            response = requests.post(api_url, json=payload, headers=headers)

            if response.status_code == 200:
                result_json = response.json()  
                st.success("API call successful!")
                st.json(result_json) 

                bucket_name = result_json.get("video_record_s3_bucket")
                object_name = result_json.get("video_response_s3_object_name")

                s3_client = boto3.client(service_name='s3')
                if bucket_name and object_name:
                    st.info(f"Fetching video from S3: {object_name}")                    
                    s3_url = s3_client.generate_presigned_url('get_object',
                    Params={'Bucket': bucket_name, 'Key': object_name},
                    ExpiresIn=600
                    )
                    st.info("Video file is ready to download.")
                    st.markdown(
                f"""
                <a href="{s3_url}" download target="_blank" style="text-decoration: none;">
                    <button style="padding: 10px 20px; font-size: 16px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
                        Download Video
                    </button>
                </a>
                """,
                unsafe_allow_html=True
                    )
                    
                else:
                    st.error("Bucket name or object name missing in the API response.")
        except requests.exceptions.RequestException as e:
            st.error("Error calling the API")
            st.write(str(e))



# import streamlit as st
# import boto3
# import os
# import json
# from datetime import datetime
# from multiprocessing import Process, Value
# from dotenv import load_dotenv
# from delete_tmp_files import clear_files_in_folder, check_folder_exists, check_file_exists
# from screen_recording import record_screen
# from s3 import upload_to_s3, append_log_to_s3
# from main_entry import main

# # Load environment variables
# load_dotenv()

# # Initialize S3 client
# s3_client = boto3.client(service_name="s3")
# bucket_name = "computerusebucket"
# log_file_name = "log_file.csv"

# # Global variables
# recording_flag = Value('b', True)
# save_dir = os.getenv("RESUTS_DIR", "./results/")

# # Streamlit configuration
# st.set_page_config(page_title="Computer Use API", layout="wide")
# st.title("Computer Use API")
# st.sidebar.title("Actions")

# # Helper functions
# def run_task(task_name, instruction, save_dir, recording_flag):
#     try:
#         process_start_time = datetime.now()
#         video_record_name = f"screen_recording_{process_start_time.strftime('%Y%m%d_%H%M%S')}.mp4"

#         # Ensure save directory exists
#         os.makedirs(save_dir, exist_ok=True)

#         # Start screen recording
#         screen_process = Process(target=record_screen, kwargs={
#             "output_file": os.path.join(save_dir, video_record_name),
#             "recording_flag": recording_flag
#         })
#         screen_process.start()

#         # Call main function with instruction
#         import sys
#         sys.argv = ["main_entry.py", instruction, "False"]
#         g = {}
#         main(g)
#         last_api_response = g.get("last_api_response")

#         # Stop recording
#         recording_flag.value = False
#         screen_process.join(timeout=5)
#         if screen_process.is_alive():
#             screen_process.terminate()
#             st.warning("Screen recording process forcefully terminated.")

#         # Upload recording to S3
#         file_name = os.path.join(save_dir, video_record_name)
#         object_name = upload_to_s3(s3_client, file_name, bucket_name)
#         st.success(f"Video uploaded to S3: {object_name}")

#         # Clear local temporary files
#         clear_local_files(save_dir)

#         # Log success
#         log_data = {
#             "API_endpoint": f"/{task_name}/",
#             "start_time": process_start_time.strftime("%Y-%m-%d %H:%M:%S"),
#             "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "task_name": task_name,
#             "prompt": instruction,
#             "response": json.dumps(last_api_response),
#             "s3_video_link": object_name,
#             "status": "success"
#         }
#         append_log_to_s3(s3_client, bucket_name, log_file_name, log_data)

#         return last_api_response, object_name

#     except Exception as e:
#         st.error(f"Error: {e}")
#         return None, None


# def clear_local_files(directory):
#     if check_folder_exists(directory) and os.getenv("DELETE_TMP_FILES", "true").lower() == "true":
#         clear_files_in_folder(directory)
#         st.info(f"Cleared files in {directory}")


# # Streamlit interface
# task_options = ["Computer Use", "Testing POC"]
# task_name = st.sidebar.selectbox("Select Task", task_options)

# instruction = st.sidebar.text_area("Enter Instruction", "")

# if st.sidebar.button("Run Task"):
#     if instruction.strip():
#         st.info(f"Running task: {task_name}")
#         response, s3_object = run_task(task_name, instruction, save_dir, recording_flag)

#         if response:
#             st.success("Task completed successfully!")
#             st.json(response)
#             st.write(f"Video uploaded to S3 bucket: {bucket_name}")
#             st.write(f"S3 Object Name: {s3_object}")
#         else:
#             st.error("No API response recorded.")
#     else:
#         st.warning("Please enter a valid instruction.")

# # Display logs
# if st.sidebar.checkbox("Show Logs"):
#     try:
#         log_data = extract_logs_from_s3(s3_client, bucket_name, log_file_name)
#         st.subheader("API Logs")
#         st.dataframe(log_data)
#     except Exception as e:
#         st.error(f"Error fetching logs: {e}")
