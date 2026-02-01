# notification_lambda.py
import json

def lambda_handler(event, context):
    print("📨 Notification Event:", event)

    for record in event["Records"]:
        body = json.loads(record["body"])
        print("🔔 Notification received:", body)

    return {"status": "notified"}
