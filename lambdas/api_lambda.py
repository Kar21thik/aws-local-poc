"""
API Lambda - Handles HTTP requests from API Gateway
Replaces FastAPI for serverless deployment
"""

import json
import os
import uuid
from app.config import get_aws_client

TASK_QUEUE_URL = os.environ.get("TASK_QUEUE_URL")

def submit_order(event, context):
    """
    POST /orders - Submit new order
    """
    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))
        items = body.get("items", [])
        promo_code = body.get("promo_code", "")
        
        # Validate
        if not items:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Items required"})
            }
        
        # Generate order ID
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Send to task queue
        sqs = get_aws_client("sqs")
        sqs.send_message(
            QueueUrl=TASK_QUEUE_URL,
            MessageBody=json.dumps({
                "order_id": order_id,
                "items": items,
                "promo_code": promo_code
            })
        )
        
        return {
            "statusCode": 202,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "order_id": order_id,
                "status": "queued",
                "message": "Order submitted for processing"
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def get_order_status(event, context):
    """
    GET /orders/{order_id} - Get order status
    """
    order_id = event["pathParameters"]["order_id"]
    
    # TODO: Query DynamoDB for order status
    return {
        "statusCode": 200,
        "body": json.dumps({
            "order_id": order_id,
            "status": "processing"
        })
    }
