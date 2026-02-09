
## Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         START                     
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                         
│  ├─ Order ID: ORD-12345                                             │
│  ├─ Items: [Laptop $200.99, Mouse $30.99 x2, Keyboard $12.99]      │
│                                             
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          task-queue (SQS)                          │
│  Message waiting in queue...                                        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (Event Source Mapping)
                                    │ AWS Lambda polls queue
                                    │ every few seconds
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│               task_lambda.lambda_handler() TRIGGERED               │
│  File: lambdas/task_lambda.py                                       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  STEP 1: Extract Order Data (input json)      │
        │  ├─ Parse JSON from SQS message               │
        │  ├─ order_id = "ORD-12345"                    │
        │  ├─ items = [...]                             │
        │                      │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  STEP 2: Validate Order                       │
        │   Call: validate_order(items)               │
        │  File: app/processors.py                      │
        │  ├─ Check if items list is not empty          │
        │  ├─ Check each item quantity > 0              │
        │  ├─ Check each item price > 0                 │
        │  └─ Return: True                            │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  STEP 3: Calculate Subtotal                   │
        │   Call: calculate_order_total(items)        │
        │  File: app/processors.py                      │
        │  ├─ Laptop: $200.99 × 1 = $200.99            │
        │  ├─ Mouse: $30.99 × 2 = $61.98               │
        │  ├─ Keyboard: $12.99 × 1 = $12.99            │
        │  └─ Return: $275.96                           │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  STEP 5: Build Invoice                        │
        │   Call: build_invoice(...)                  │
        │  File: app/processors.py                      │
        │  ├─ Create invoice dictionary                 │
        │  ├─ Add order_id, items, totals               │
        │  ├─ Add timestamp and status                  │
        │  └─ Return: {invoice_object}                  │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  STEP 6: Save to S3                           │
        │   Call: save_to_s3(bucket, key, invoice)    │
        │  File: app/storage.py                         │
        │  ├─ get_aws_client("s3")                      │
        │  │   └─ File: app/config.py                   │
        │  ├─ Convert invoice to JSON                   │
        │  ├─ s3.put_object()                           │
        │  └─ Saved: s3://results-bucket/ORD-12345.json│
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  STEP 7: Send Notification                    │
        │   Call: send_notification(queue_url, msg)   │
        │  File: app/notifier.py                        │
        │  ├─ get_aws_client("sqs")                     │
        │  │   └─ File: app/config.py                   │
        │  ├─ Create notification message               │
        │  ├─ sqs.send_message()                        │
        │  └─ Sent to notification-queue                │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     notification-queue (SQS)                       │
│  Message: {"order_id": "ORD-12345", "status": "processed", ...}    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (Event Source Mapping)
                                    │ AWS Lambda polls queue
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│          notification_lambda.lambda_handler() TRIGGERED            │
│  File: lambdas/notification_lambda.py                               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────┐
        │  Parse Notification Message                   │
        │  ├─ Extract order_id                          │
        │  ├─ Extract status                            │
        │  ├─ Extract final_total                       │
        │  └─ Print notification log                    │
        └───────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          ORDER COMPLETE                            │
│  - Invoice saved in S3                                              │
│  - Notification logged                                              │
│  - Customer can be notified (email/SMS in production)               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Function Call Hierarchy

```
task_lambda.lambda_handler()
│
├─► validate_order(items)                    [app/processors.py]
│   └─► Returns: True/False
│
├─► calculate_order_total(items)             [app/processors.py]
│   └─► Returns: subtotal (float)
│
├─► apply_discount(subtotal, promo_code)     [app/processors.py]
│   └─► Returns: (final_total, discount_amount)
│
├─► build_invoice(...)                       [app/processors.py]
│   └─► Returns: invoice (dict)
│
├─► save_to_s3(bucket, key, invoice)         [app/storage.py]
│   ├─► get_aws_client("s3")                 [app/config.py]
│   └─► s3.put_object()
│
└─► send_notification(queue_url, message)    [app/notifier.py]
    ├─► get_aws_client("sqs")                [app/config.py]
    └─► sqs.send_message()
```

---

## Detailed Function Flow with Data

### Example Order Processing:

```
INPUT:
{
  "order_id": "ORD-12345",
  "items": [
    {"name": "Laptop", "price": 200.99, "quantity": 1},
    {"name": "Mouse", "price": 30.99, "quantity": 2},
    {"name": "Keyboard", "price": 12.99, "quantity": 1}
  ],
  "promo_code": "SAVE10"
}

FLOW:
┌──────────────────────────────────────────────────────────────┐
│ 1. validate_order(items)                                     │
│    Input: [3 items]                                          │
│    Output: True ✅                                           │
└──────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. calculate_order_total(items)                              │
│    Input: [3 items]                                          │
│    Calculation:                                              │
│      200.99 × 1 = 200.99                                     │
│      30.99 × 2 = 61.98                                       │
│      12.99 × 1 = 12.99                                       │
│    Output: 275.96                                            │
└──────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. apply_discount(275.96, "SAVE10")                          │
│    Input: subtotal=275.96, promo="SAVE10"                    │
│    Calculation:                                              │
│      Discount rate: 10%                                      │
│      Discount amount: 275.96 × 0.10 = 27.60                 │
│      Final total: 275.96 - 27.60 = 248.36                   │
│    Output: (248.36, 27.60)                                   │
└──────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. build_invoice(...)                                        │
│    Input: All order data + calculated values                 │
│    Output: {                                                 │
│      "order_id": "ORD-12345",                                │
│      "items": [...],                                         │
│      "item_count": 3,                                        │
│      "subtotal": 275.96,                                     │
│      "promo_code": "SAVE10",                                 │
│      "discount": 27.60,                                      │
│      "final_total": 248.36,                                  │
│      "status": "completed",                                  │
│      "timestamp": 1704067200.0                               │
│    }                                                         │
└──────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. save_to_s3("results-bucket", "ORD-12345.json", invoice)  │
│    ├─ get_aws_client("s3")                                   │
│    ├─ Convert invoice to JSON string                         │
│    └─ Upload to S3                                           │
│    Result: s3://results-bucket/ORD-12345.json created        │
└──────────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. send_notification(queue_url, notification_msg)            │
│    ├─ get_aws_client("sqs")                                  │
│    └─ Send message to notification-queue                     │
│    Message: {                                                │
│      "order_id": "ORD-12345",                                │
│      "status": "processed",                                  │
│      "final_total": 248.36,                                  │
│      "invoice_location": "s3://results-bucket/ORD-12345.json"│
│    }                                                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Infrastructure Setup Flow (Notebook Cells)

```
┌─────────────────────────────────────────────────────────────┐
│  Cell 1: Import Libraries                                   │
│  └─ boto3, json, time                                       │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  Cell 2: Create Infrastructure                              │
│  ├─ Create S3 bucket: results-bucket                        │
│  ├─ Create SQS queue: task-queue                            │
│  ├─ Create SQS queue: notification-queue                    │
│  └─ Create IAM role: lambda-role                            │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  Cell 3: Package & Deploy Lambda Functions                  │
│  ├─ create_lambda_zip()                                     │
│  │   ├─ Add app/*.py files                                  │
│  │   └─ Add lambdas/*.py files                              │
│  ├─ Deploy task_lambda                                      │
│  │   └─ Handler: task_lambda.lambda_handler                 │
│  └─ Deploy notification_lambda                              │
│      └─ Handler: notification_lambda.lambda_handler          │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  Cell 4: Create Event Source Mappings                       │
│  ├─ add_trigger(task-queue, task_lambda)                    │
│  │   └─ Links: task-queue → task_lambda                     │
│  └─ add_trigger(notification-queue, notification_lambda)    │
│      └─ Links: notification-queue → notification_lambda     │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  Cell 5: Send Test Order                                    │
│  └─ sqs.send_message(task-queue, order_data)                │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  Cell 6: Verify Results                                     │
│  ├─ Wait 10 seconds                                         │
│  ├─ Check S3 for invoice                                    │
│  └─ Display invoice details                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## File Dependencies Map

```
task_lambda.py
    │
    ├─ imports from ──► app/processors.py
    │                      ├─ validate_order()
    │                      ├─ calculate_order_total()
    │                      ├─ apply_discount()
    │                      └─ build_invoice()
    │
    ├─ imports from ──► app/storage.py
    │                      └─ save_to_s3()
    │                          └─ imports from ──► app/config.py
    │                                                └─ get_aws_client()
    │
    └─ imports from ──► app/notifier.py
                           └─ send_notification()
                               └─ imports from ──► app/config.py
                                                     └─ get_aws_client()

notification_lambda.py
    └─ (No imports - standalone)
```

---

## AWS Service Interaction Flow

```
┌──────────────┐
│   Jupyter    │
│   Notebook   │
└──────┬───────┘
       │ boto3 calls
       ▼
┌──────────────────────────────────────────────────────────┐
│              LocalStack (localhost:4566)                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │    SQS     │  │     S3     │  │   Lambda   │        │
│  │  Queues    │  │   Bucket   │  │ Functions  │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└──────────────────────────────────────────────────────────┘
       │                 │                 │
       │                 │                 │
       ▼                 ▼                 ▼
   Messages          Invoices         Executions
   stored in         saved as         run in Docker
   queues            JSON files       containers
```

---

## Summary

This system demonstrates a complete **event-driven serverless architecture**:

1. **Order arrives** → Sent to task-queue
2. **Lambda automatically triggered** → Processes order through 6 steps
3. **Functions called in sequence** → validate → calculate → discount → invoice → save → notify
4. **Notification sent** → Triggers second Lambda
5. **Workflow complete** → Invoice in S3, notification logged

**Key Point:** Everything happens automatically after the initial order is sent. No manual intervention needed!
