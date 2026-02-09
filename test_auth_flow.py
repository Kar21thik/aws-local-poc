# Test JWT Authorization Flow
# Run this after deploying infrastructure

import boto3
import json
import time
from api.auth import create_token, verify_token

ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
TASK_QUEUE_NAME = "task-queue"

sqs = boto3.client("sqs", endpoint_url=ENDPOINT_URL, region_name=REGION)
s3 = boto3.client("s3", endpoint_url=ENDPOINT_URL, region_name=REGION)

def get_queue_url():
    return sqs.get_queue_url(QueueName=TASK_QUEUE_NAME)['QueueUrl']

print("=" * 70)
print("🔐 JWT AUTHORIZATION FLOW TEST")
print("=" * 70)

# Step 1: Generate JWT Token
print("\n📝 Step 1: Generate JWT Token")
user_id = "test-user-123"
token = create_token(user_id)
print(f"   User ID: {user_id}")
print(f"   Token: {token[:50]}...")

# Step 2: Verify Token (simulating API Gateway Authorizer)
print("\n🔍 Step 2: Verify Token (Lambda Authorizer)")
result = verify_token(token)
if result["valid"]:
    print(f"   ✅ Token Valid")
    print(f"   User ID Extracted: {result['user_id']}")
else:
    print(f"   ❌ Token Invalid: {result['error']}")
    exit(1)

# Step 3: Send Message to SQS with user_id
print("\n📤 Step 3: Send Order to SQS Queue (with user_id)")
order_id = f"AUTH-TEST-{int(time.time())}"
order_message = {
    "order_id": order_id,
    "user_id": user_id,  # Extracted from JWT
    "items": [
        {"name": "Laptop", "price": 999.99, "quantity": 1},
        {"name": "Mouse", "price": 29.99, "quantity": 2}
    ],
    "promo_code": "SAVE10"
}

queue_url = get_queue_url()
sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(order_message))
print(f"   Order ID: {order_id}")
print(f"   User ID in Message: {user_id}")
print(f"   Items: {len(order_message['items'])}")

# Step 4: Wait for Lambda Processing
print("\n⏳ Step 4: Waiting for Consumer Lambda to Process...")
print("   (Lambda will validate user_id from message)")
time.sleep(10)

# Step 5: Verify Result
print("\n✅ Step 5: Verify Processing Result")
try:
    obj = s3.get_object(Bucket="results-bucket", Key=f"{order_id}.json")
    invoice = json.loads(obj['Body'].read())
    
    print(f"   ✅ Invoice Created Successfully!")
    print(f"   Order ID: {invoice['order_id']}")
    print(f"   User ID: {invoice.get('user_id', 'N/A')}")
    print(f"   Final Total: ${invoice['final_total']}")
    print(f"   Status: {invoice['status']}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print("\n" + "=" * 70)
print("🎉 JWT AUTHORIZATION FLOW COMPLETE")
print("=" * 70)

# Test Unauthorized Access
print("\n\n🚫 Testing Unauthorized Access (missing user_id)...")
bad_order = {
    "order_id": f"UNAUTH-{int(time.time())}",
    # Missing user_id
    "items": [{"name": "Test", "price": 10, "quantity": 1}]
}
sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(bad_order))
print("   Sent order without user_id")
print("   ⏳ This should fail and go to DLQ...")
time.sleep(15)
print("   ✅ Check DLQ for unauthorized message")
