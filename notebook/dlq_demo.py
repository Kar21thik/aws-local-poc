# Cell 6: Complete DLQ Demo - Fail → Retry → DLQ → Process → Fetch Results

import time
import json

# Step 1: Configure fast retries
sqs.set_queue_attributes(QueueUrl=TASK_QUEUE_URL, Attributes={'VisibilityTimeout': '5'})

# Step 2: Send order with negative price (will fail in task_lambda, but DLQ will fix it)
order_id = f"DLQ-TEST-{int(time.time())}"
bad_order = {
    "order_id": order_id,
    "items": [{"name": "Laptop", "price": -999.99, "quantity": -2}],  # Negative values
    "promo_code": "SAVE10"
}

print(f"🧪 DLQ DEMO: {order_id}")
print("="*60)
print(f"💥 Sending BAD order (negative price/quantity)...")
sqs.send_message(QueueUrl=TASK_QUEUE_URL, MessageBody=json.dumps(bad_order))

# Step 3: Wait for DLQ processing (retry + DLQ + fix)
print(f"⏳ Waiting 20s for: fail → retry → DLQ → fix → save...")
time.sleep(20)

# Step 4: Fetch the recovered invoice from S3
print(f"\n📥 Fetching recovered invoice from S3...")
try:
    response = s3.get_object(Bucket=BUCKET_NAME, Key=f"{order_id}.json")
    invoice = json.loads(response['Body'].read())
    
    print(f"✅ SUCCESS - Order recovered by DLQ!")
    print(f"\n📄 Invoice Details:")
    print(f"   Order ID: {invoice['order_id']}")
    print(f"   Subtotal: ${invoice['subtotal']}")
    print(f"   Discount: ${invoice['discount_amount']}")
    print(f"   Final Total: ${invoice['final_total']}")
    print(f"   Recovered from DLQ: {invoice.get('recovered_from_dlq', False)}")
    print(f"   Fixes Applied: {invoice.get('dlq_fixes', [])}")
    
except Exception as e:
    print(f"❌ Invoice not found: {e}")
    print(f"   DLQ may still be processing or order couldn't be fixed")

print("="*60)
