import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

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