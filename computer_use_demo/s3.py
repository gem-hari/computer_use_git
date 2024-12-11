import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import csv
import io
import pandas as pd
from io import StringIO

#s3_client = boto3.client(service_name='s3')

def upload_to_s3(s3_client,file_name, bucket, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_name) 
    try:
        s3_client.upload_file(file_name, bucket, object_name)
        print(f"File {file_name} uploaded to {bucket}/{object_name}")
        return object_name
    except FileNotFoundError:
        print(f"The file {file_name} was not found")
        return None
    except NoCredentialsError:
        print("Credentials not available")
        return None
    except PartialCredentialsError:
        print("Incomplete credentials provided")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def delete_from_s3(s3_client,bucket_name, object_key):
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        print(f"Deleted {object_key} from bucket {bucket_name}")
        return True
    except NoCredentialsError:
        print("Credentials not available")
        return False
    except PartialCredentialsError:
        print("Incomplete credentials provided")
        return False
    except Exception as e:
        print(f"An error occurred while deleting from S3: {e}")
        return False
    

def extract_file_from_s3(s3_client,bucket, object_name):
    try:
        s3_response = s3_client.get_object(Bucket=bucket, Key=object_name)
        print(f"Object Retrived from {bucket}/{object_name}")
        return s3_response
    except Exception as e:
        print(f"An error occurred: {e}")
        return exit(1)



def append_log_to_s3(s3_client, bucket, log_file_name, log_data):
    try:
        # Check if the log file already exists in the S3 bucket
        existing_data = None
        try:
            response = s3_client.get_object(Bucket=bucket, Key=log_file_name)
            existing_data = response['Body'].read().decode('utf-8')
        except s3_client.exceptions.NoSuchKey:
            print(f"{log_file_name} does not exist. Creating a new file.")

        # Load existing data into a DataFrame (if it exists)
        if existing_data:
            csv_buffer = StringIO(existing_data)
            df = pd.read_csv(csv_buffer)
        else:
            # Create an empty DataFrame with the required columns
            df = pd.DataFrame(columns=["API_endpoint", "start_time", "end_time", "task_name", "prompt", "response", "s3_video_link", "status"])

        # Ensure log_data is structured as a single-row DataFrame
        new_data = pd.DataFrame([log_data])

        # Concatenate the new data with the existing DataFrame
        df = pd.concat([df, new_data], ignore_index=True)

        # Write the updated DataFrame back to S3
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        s3_client.put_object(Bucket=bucket, Key=log_file_name, Body=csv_buffer.getvalue())
        print("Log successfully updated in S3.")

    except Exception as e:
        print(f"Error occurred while appending log to S3: {e}")
