# task_lambda.py
import json
import os
from app.processors import calculate_sum, build_result , calculate_average 
from app.storage import save_to_s3
from app.notifier import send_notification
from app.config import get_aws_client

# Config
BUCKET = "results-bucket"
QUEUE_NAME = "notification-queue"

# Construct SQS URL dynamically
endpoint = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566").rstrip("/")
NOTIFICATION_QUEUE_URL = f"{endpoint}/000000000000/{QUEUE_NAME}"

def lambda_handler(event, context):
    print("📥 Event received:", event)

    for record in event.get("Records", []):
        body = json.loads(record["body"])
        
        task_id = body.get("task_id")
        numbers = body.get("numbers", [])
        
        print(f"🔹 Processing Task: {task_id}")

        # Process data
        total_sum = calculate_sum(numbers)
        result = build_result(task_id, total_sum)

        # Save to S3
        key = f"{task_id}.json"
        save_to_s3(BUCKET, key, result)

        # Notify next step
        send_notification(NOTIFICATION_QUEUE_URL, {
            "task_id": task_id,
            "status": "processed",
            "result_location": f"s3://{BUCKET}/{key}"
        })

    return {"status": "success"}
