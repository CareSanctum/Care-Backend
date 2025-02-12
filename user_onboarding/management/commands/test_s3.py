import boto3

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Test AWS S3 connection"

    def handle(self, *args, **kwargs):
        s3 = boto3.client(
            "s3",
            aws_access_key_id= os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_S3_REGION_NAME"),
        )

# List all objects in the bucket
        bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")

        try:
            response = s3.list_objects_v2(Bucket=bucket_name)
            if "Contents" in response:
                print("✅ S3 Connection Successful! Files in bucket:")
                for obj in response["Contents"]:
                    print(obj["Key"])
            else:
                print("✅ S3 Connected, but the bucket is empty.")
        except Exception as e:
            print("❌ S3 Connection Failed:", str(e))
