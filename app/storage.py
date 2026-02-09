# app/storage.py
import json
import logging
from app.config import get_aws_client

logger = logging.getLogger(__name__)

def save_to_s3(bucket_name, file_key, data):
    """
    Saves dictionary data as JSON file in S3.
    """
    try:
        s3 = get_aws_client("s3")
        s3.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=json.dumps(data, indent=2)
        )
        logger.info(f"   ✅ Saved to s3://{bucket_name}/{file_key}")
        
    except Exception as e:
        logger.error(f"   ❌ S3 save failed: {str(e)}")
        raise
