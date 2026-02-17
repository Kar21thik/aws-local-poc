# accessing through the api endpoint (single and bulk inputs)
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import boto3
import json
import uuid
import os
from typing import List
from api.auth import create_token, verify_token
from api.models import Order
from app.parameter_store import get_cached_parameter

app = FastAPI(title="Order Processing API", version="1.0.0")
security = HTTPBearer()

ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
REGION = os.getenv("AWS_REGION", "us-east-1")

sqs = boto3.client("sqs", endpoint_url=ENDPOINT_URL, region_name=REGION)

def get_queue_url_from_params(param_name):
    return get_cached_parameter(param_name)

def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    result = verify_token(token)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=result.get("error", "Invalid token"))
    return result["user_id"]

@app.get("/")
def root():
    return {"message": "Order Processing API", "docs": "/docs"}

@app.post("/token")
def generate_token(user_id: str = "test-user"):
    token = create_token(user_id)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/orders")
def submit_order(order: dict, user_id: str = Depends(verify_jwt)):
    try:
        order_obj = Order(**order)
        order_obj.validate()
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    correlation_id = str(uuid.uuid4())
    order_id = f"ORD-{int(uuid.uuid4().time_low)}"
    
    message = {
        "correlation_id": correlation_id,
        "order_id": order_id,
        "items": order["items"],
        "promo_code": order.get("promo_code"),
        "user_id": user_id
    }
    
    queue_url = get_queue_url_from_params("poc-task-queue-url")
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))
    
    return {
        "status": "submitted",
        "order_id": order_id,
        "correlation_id": correlation_id
    }

@app.post("/orders/batch")
def submit_batch_orders(orders: List[dict], user_id: str = Depends(verify_jwt)):
    results = []
    
    for order in orders:
        try:
            order_obj = Order(**order)
            order_obj.validate()
            
            correlation_id = str(uuid.uuid4())
            order_id = f"ORD-{int(uuid.uuid4().time_low)}"
            
            message = {
                "correlation_id": correlation_id,
                "order_id": order_id,
                "items": order["items"],
                "promo_code": order.get("promo_code"),
                "user_id": user_id
            }
            
            queue_url = get_queue_url_from_params("poc-task-queue-url")
            sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message))
            
            results.append({
                "status": "submitted",
                "order_id": order_id,
                "correlation_id": correlation_id
            })
            
        except (TypeError, ValueError) as e:
            results.append({"status": "failed", "error": str(e)})
        except Exception as e:
            results.append({"status": "failed", "error": f"SQS error: {str(e)}"})
    
    return {"total": len(orders), "results": results}

@app.get("/dlq/stats")
def get_dlq_stats(user_id: str = Depends(verify_jwt)):
    try:
        dlq_url = get_queue_url_from_params("poc-dlq-queue-url")
        attrs = sqs.get_queue_attributes(
            QueueUrl=dlq_url,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        return {
            "queue": "task-dlq",
            "messages_available": int(attrs['Attributes'].get('ApproximateNumberOfMessages', 0)),
            "messages_in_flight": int(attrs['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dlq/messages")
def get_dlq_messages(user_id: str = Depends(verify_jwt)):
    try:
        dlq_url = get_queue_url_from_params("poc-dlq-queue-url")
        response = sqs.receive_message(
            QueueUrl=dlq_url,
            MaxNumberOfMessages=10,
            VisibilityTimeout=30,
            WaitTimeSeconds=1
        )
        
        messages = []
        for msg in response.get('Messages', []):
            body = json.loads(msg['Body'])
            messages.append({
                "message_id": msg['MessageId'],
                "order_id": body.get('order_id'),
                "correlation_id": body.get('correlation_id'),
                "receipt_handle": msg['ReceiptHandle'],
                "body": body
            })
        
        return {"count": len(messages), "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
