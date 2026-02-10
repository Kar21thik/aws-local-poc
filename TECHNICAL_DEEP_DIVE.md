
Event-Driven Order Processing with SQS + Lambda + S3

Client → task-queue (SQS) → task_lambda → S3 + notification-queue → notification_lambda
                                ↓ (on failure after 2 retries)
                              task-dlq → dlq_processor_lambda


Detailed Step-by-Step Flow

 Step 1: Message Ingestion

  ```python
  {
    "order_id": "ORD-12345",
    "items": [{"name": "Laptop", "price": 999.99, "quantity": 1}],
    "promo_code": "SAVE10"
  }
  ```
- AWS Call:`sqs.send_message(QueueUrl=TASK_QUEUE_URL, MessageBody=json.dumps(message))`
- Result: Message lands in `task-queue` with visibility timeout of 180s

---

Step 2: Lambda Trigger (Automatic)
- Trigger: SQS Event Source Mapping polls `task-queue` every few seconds
- Batch Size: 10 messages 
- Invocation: AWS Lambda service invokes `task_lambda.lambda_handler(event, context)`
- Event Structure:
  ```python
  {
    "Records": [
      {
        "body": "{\"order_id\": \"ORD-12345\", ...}",
        "messageId": "...",
        "receiptHandle": "..."
      }
    ]
  }
  ```


Step 3: Order Processing 
File: `lambdas/task_lambda.py::lambda_handler()`

Line-by-Line Execution:

1. Parse Message 
   ```python
   body = json.loads(record["body"])
   order_id = body.get("order_id")
   items = body.get("items", [])
   promo_code = body.get("promo_code", "")
   ```

2. Validate Items
   ```python
   for item in items:
       if item.get("price", 0) < 0 or item.get("quantity", 0) <= 0:
           raise ValueError(...)  
   ```

3.Calculate Subtotal
   - Calls: `app/processors.py::calculate_order_total(items)`
   - Logic: `sum(item["price"] * item["quantity"] for item in items)`
  

4. **Apply Discount 
   - Calls: `app/processors.py::apply_discount(subtotal, promo_code)`
   - Logic: Lookup promo code in dict, calculate discount
   

5. **Calculate Bulk Discount  [NESTED FOLDER TEST]
   - Calls: `app/helpers/discount_calculator.py::calculate_bulk_discount(subtotal)`
   - Proves: Lambda can access nested modules (`app/helpers/`)
   - AWS Calls: None

6. Build Invoice 
   - Calls: `app/processors.py::build_invoice(...)`
   - Logic: Constructs JSON object with all order details
   

7. Save to S3 
   - Calls: `app/storage.py::save_to_s3(BUCKET, key, invoice)`
   - AWS Call:`s3.put_object(Bucket="results-bucket", Key="ORD-12345.json", Body=json.dumps(invoice))`
   - Result:Invoice persisted to S3

8. Send Notification 
   - Calls: `app/notifier.py::send_notification(NOTIFICATION_QUEUE_URL, message)`
   - AWS Call: `sqs.send_message(QueueUrl=notification_queue_url, MessageBody=json.dumps(message))`
   - Result: Message lands in `notification-queue`



Step 4: Notification Processing


- Trigger:SQS Event Source Mapping on `notification-queue`
- Action: Logs notification 
- AWS Calls:  (just logging)



Step 5: Failure Handling (DLQ)


- Trigger: Message fails 2 times in `task-queue` → moved to `task-dlq`
- Action: Logs error, attempts to fix data, reprocesses
- AWS Calls:
  - `s3.put_object()` - Save recovered order
  - Potentially `sqs.send_message()` - Requeue fixed message





Orchestrators (Lambda Handlers)



`task_lambda.py`  Main order processor  SQS: task-queue  S3 (write), SQS (send) 
`notification_lambda.py`  Notification handler  SQS: notification-queue  None (logs only) 
`dlq_processor_lambda.py`  Error recovery  SQS: task-dlq  S3 (write), SQS (send) 








Problem 1: Synchronous S3 Writes**
Location: `app/storage.py::save_to_s3()`
```python
s3.put_object(Bucket=bucket_name, Key=file_key, Body=json.dumps(data))
```
Issue: Each Lambda waits for S3 write to complete (~50-200ms)  
Impact at 5,000 messages:
- 5,000 concurrent Lambda invocations
- Each blocks on S3 write
- Total time: ~200ms per order (sequential)
- Bottleneck: S3 API rate limits (3,500 PUT/s per prefix)
```python

import asyncio
await s3_client.put_object(...)
```
---

Problem 2: No Batch Processing
```python
for record in event.get("Records", []):  
    
```
Issue: Processes messages sequentially in loop  
Impact: 10 messages = 10 × processing time

**Fix (Option 1 - Threading):**
```python
# Uses threads - good for I/O-bound tasks (S3, SQS calls)
import concurrent.futures

def lambda_handler(event, context):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_order, record) for record in event["Records"]]
        concurrent.futures.wait(futures)
```

**Fix (Option 2 - Async/Await - Better for Lambda):**
```python
# Uses asyncio - more efficient for AWS SDK calls
import asyncio
import aioboto3

async def process_order_async(record):
    # Process order with async AWS calls
    pass

def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    tasks = [process_order_async(record) for record in event["Records"]]
    loop.run_until_complete(asyncio.gather(*tasks))
```

**Why Threading Works Here:**
- Lambda processing is I/O-bound (waiting for S3, SQS)
- Python GIL doesn't block I/O operations
- Threads share memory (efficient in Lambda)

**Threading vs Multiprocessing:**
- Threading: Shares memory, good for I/O (S3, SQS, network)
- Multiprocessing: Separate memory, good for CPU-heavy tasks
- Lambda: Use threading or async (multiprocessing adds overhead)


Problem 5: Partial Batch Failure

```python
for record in event.get("Records", []):
    # If one message fails, entire batch fails
    process_order(record)
```
Issue: If message #5 fails in batch of 10, all 10 messages return to queue  
Impact: Messages #1-4 and #6-10 reprocess unnecessarily

**Fix:**
```python
failed_messages = []
for record in event["Records"]:
    try:
        process_order(record)
    except Exception as e:
        failed_messages.append({"itemIdentifier": record["messageId"]})
        
return {"batchItemFailures": failed_messages}  
```

-

-
---

Problem 8: Cold Start Latency
Location: All Lambda functions
```python
import boto3  
```
Issue: First invocation takes 1-3 seconds (cold start)  
Impact: High P99 latency


 No Circuit Breaker for S3

```python
s3.put_object(...)  
```
Issue: If S3 is down, all Lambda invocations fail  
Impact: Messages move to DLQ unnecessarily





