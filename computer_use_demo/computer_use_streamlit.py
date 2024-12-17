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
        api_url = "http://127.0.0.1:8001/computer_use/"
    else:
        api_url = "http://127.0.0.1:8001/testing_poc/"

    if instruction.strip() == "":
        st.error("Please enter a valid instruction.")
    else:
        headers = {"Content-Type": "application/json"}
        payload = {"instruction": instruction,
        "use_case": task_type}
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