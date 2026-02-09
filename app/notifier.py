# app/notifier.py
import json
import logging
from app.config import get_aws_client

logger = logging.getLogger(__name__)

def send_notification(queue_url, message):
    """
    Sends message to SQS queue.
    """
    try:
        sqs = get_aws_client("sqs")
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        logger.info(f"   ✅ Notification sent to queue")
        
    except Exception as e:
        logger.error(f"   ❌ Notification failed: {str(e)}")
        raise






