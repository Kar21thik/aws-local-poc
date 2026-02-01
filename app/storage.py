# app/storage.py
import json
from app.config import get_aws_client

def save_to_s3(bucket_name, file_key, data):
    """
    Saves dictionary data as JSON file in S3.
    """
    s3 = get_aws_client("s3")

    s3.put_object(
        Bucket=bucket_name,
        Key=file_key,
        Body=json.dumps(data)
    )

    print(f"✅ Saved file to S3 -> {bucket_name}/{file_key}")
