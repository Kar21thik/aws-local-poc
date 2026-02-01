# app/notifier.py
import json
from app.config import get_aws_client

def send_notification(queue_url, message):
    """
    Sends message to SQS queue.
    """
    sqs = get_aws_client("sqs")

    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )

    print(f"📨 Notification sent to queue: {queue_url}")
