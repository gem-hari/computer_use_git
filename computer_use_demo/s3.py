import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import csv
import io

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




def append_log_to_s3(s3_client, bucket, object_name, log_data):
    """
    Append a log entry to a CSV file stored in S3. Create the file if it doesn't exist.
    """
    try:
        # Try to fetch the existing file from S3
        csv_buffer = io.StringIO()
        try:
            response = s3_client.get_object(Bucket=bucket, Key=object_name)
            existing_data = response['Body'].read().decode('utf-8')
            csv_buffer.write(existing_data)
        except s3_client.exceptions.NoSuchKey:
            # File does not exist, create a new one
            print("Log file not found, creating a new one.")

        # Create a CSV writer and append the log
        writer = csv.DictWriter(csv_buffer, fieldnames=[
            "API_endpoint", "start_time", "end_time", "task_name", "prompt",
            "response", "s3_video_link", "status"
        ])
        if csv_buffer.tell() == 0:  # Check if buffer is empty (new file)
            writer.writeheader()
        writer.writerow(log_data)

        # Upload updated CSV back to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=object_name,
            Body=csv_buffer.getvalue()
        )
        print(f"Log successfully updated in {bucket}/{object_name}")

    except Exception as e:
        print(f"Error while updating log in S3: {e}")
