import streamlit as st
import boto3

s3_client = boto3.client(service_name='s3')

with st.form("instruction_form"):
    submit_button = st.form_submit_button("Submit")

if submit_button:
    bucket_name = "computerusebucket"
    object_name = "screen_recording_20241205_055213_.mp4"

    if bucket_name and object_name:
        try:
            # Generate pre-signed URL for the video
            s3_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=3600  # URL expires in 1 hour
            )
            
            # Display an info message
            st.info("Video file is ready to download.")
            
            # Create a download button
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
        except Exception as e:
            st.error("Error fetching pre-signed URL")
            st.write(str(e))
    else:
        st.error("Bucket name or object name missing in the API response.")
