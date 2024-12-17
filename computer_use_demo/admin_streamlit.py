import streamlit as st
import boto3
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
import os
from s3 import fetch_csv_from_s3

load_dotenv()

# AWS S3 Configuration
S3_BUCKET_NAME = os.getenv("BUCKET_NAME")
CSV_FILE_KEY = os.getenv("ADMIN_LOG_FILE_NAME")
s3_client = boto3.client(service_name='s3')

st.title("Admin Dashboard")
with st.spinner("Loading data..."):
    data = fetch_csv_from_s3(s3_client,S3_BUCKET_NAME, CSV_FILE_KEY)
    if data is not None:
        reversed_data = data.iloc[::-1].reset_index(drop=True)
        st.dataframe(reversed_data)
        

