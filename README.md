# AWS LocalStack POC - Order Processing System

A serverless event-driven order processing system built with AWS services (Lambda, SQS, S3) running locally using LocalStack.

## 🏗️ Architecture

```
FastAPI → task-queue → task_lambda → S3 + notification-queue → notification_lambda
                ↓ (on failure)
              task-dlq → dlq_processor_lambda
```

## 📋 Features

- **Async Processing** - SQS queues for decoupled message handling
- **Lambda Functions** - Serverless order processing, notifications, and error handling
- **Dead Letter Queue** - Automatic retry (2 attempts) and failure handling
- **S3 Storage** - Invoice persistence
- **LocalStack** - Full AWS simulation locally

## 🛠️ Tech Stack

- **AWS Lambda** - Serverless compute
- **AWS SQS** - Message queuing
- **AWS S3** - Object storage
- **LocalStack** - Local AWS cloud stack
- **Docker** - Containerization
- **Python 3.10+** - Programming language

## 📁 Project Structure

```
aws-local-poc/
├── api/                    # FastAPI application
│   ├── main.py            # API endpoints
│   ├── auth.py            # JWT authentication
│   └── models.py          # Data models
├── app/                    # Shared application code
│   ├── config.py          # AWS client configuration
│   ├── processors.py      # Business logic (calculate, discount)
│   ├── storage.py         # S3 operations
│   └── notifier.py        # SQS message sender
├── lambdas/               # Lambda functions
│   ├── task_lambda.py     # Order processor
│   ├── notification_lambda.py  # Notification handler
│   └── dlq_processor_lambda.py # Failed message handler
├── notebook/
│   └── poc.ipynb          # Infrastructure setup script
├── docker-compose.yml     # LocalStack configuration
└── start_api.bat          # API startup script
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Docker Desktop
- Jupyter Notebook (optional, for setup)

### 1. Start LocalStack

```bash
docker-compose up -d
```

This starts LocalStack on `http://localhost:4566`

### 2. Setup Infrastructure

Open `notebook/poc.ipynb` and run all cells in order:

1. **Cell 1** - Initialize AWS clients
2. **Cell 2** - Create S3, SQS queues, IAM roles, DLQ
3. **Cell 3** - Deploy Lambda functions
4. **Cell 4** - Link queues to Lambda triggers
5. **Cell 5** - Test with sample order (optional)

### 3. Start FastAPI Server (optional for giving the inputs)

```bash
start_api.bat
```

Or manually:
```bash
pip install fastapi uvicorn pyjwt boto3
uvicorn api.main:app --reload --host 0.0.0.0 --port 8080
```

Access Swagger UI: http://localhost:8080/docs

## 📡 API Usage

### 1. Get JWT Token

```bash
POST http://localhost:8080/token
Body: { "user_id": "test-user" }
```

### 2. Submit Order

```bash
POST http://localhost:8080/orders
Headers: Authorization: Bearer <token>
Body: {
  "items": [
    {"name": "Laptop", "price": 999.99, "quantity": 1},
    {"name": "Mouse", "price": 29.99, "quantity": 2}
  ],
  "promo_code": "SAVE10"
}
```

### 3. Check DLQ Stats

```bash
GET http://localhost:8080/dlq/stats
Headers: Authorization: Bearer <token>
```

## 🔄 System Flow

### Normal Flow:
1. API receives order → Validates → Sends to `task-queue`
2. `task_lambda` triggered → Processes order → Calculates total → Applies discount
3. Saves invoice to S3 (`results-bucket`)
4. Sends notification to `notification-queue`
5. `notification_lambda` triggered → Logs completion

### Failure Flow (DLQ):
1. `task_lambda` fails processing
2. Message retried (2 attempts)
3. After 2 failures → Message moved to `task-dlq`
4. `dlq_processor_lambda` triggered → Logs error for manual review

## 🧪 Testing

### Test Normal Order:
```python
# In poc.ipynb Cell 5
order_message = {
    "order_id": "ORD-123",
    "items": [
        {"name": "Laptop", "price": 200.99, "quantity": 1}
    ],
    "promo_code": "SAVE10"
}
```

### Test DLQ (Trigger Failure):
```python
# Use negative price to cause Lambda failure
order_message = {
    "order_id": "ORD-456",
    "items": [
        {"name": "Invalid", "price": -100, "quantity": 1}
    ]
}
```

## 🔧 Configuration

### LocalStack Endpoints:
- **From Host Machine**: `http://localhost:4566`
- **From Docker Container**: `http://localstack:4566`

### Environment Variables:
```bash
AWS_ENDPOINT_URL=http://localhost:4566  # or http://localstack:4566 in Lambda
AWS_REGION=us-east-1
```

### Promo Codes:
- `SAVE10` - 10% discount
- `SAVE20` - 20% discount
- `SAVE30` - 30% discount
- `FREESHIP` - 5% discount

## 📊 AWS Resources Created

| Resource | Name | Purpose |
|----------|------|---------|
| S3 Bucket | `results-bucket` | Store order invoices |
| SQS Queue | `task-queue` | Order processing queue |
| SQS Queue | `notification-queue` | Notification queue |
| SQS Queue | `task-dlq` | Dead letter queue |
| Lambda | `task_lambda` | Process orders |
| Lambda | `notification_lambda` | Handle notifications |
| Lambda | `dlq_processor_lambda` | Handle failures |
| IAM Role | `lambda-role` | Lambda execution role |

## 🐛 Troubleshooting

### LocalStack not starting:
```bash
docker-compose down
docker-compose up -d
docker logs localstack_main
```

### Lambda not triggering:
```bash
# Check event source mappings in poc.ipynb
mappings = lambdas.list_event_source_mappings()
```

### View Lambda logs:
```bash
docker logs localstack_main | grep "task_lambda"
```

### Reset everything:
```bash
docker-compose down -v
docker-compose up -d
# Re-run poc.ipynb cells
```

## 📝 Key Concepts

### Event Source Mapping
Automatically triggers Lambda when messages arrive in SQS queue.

### Dead Letter Queue (DLQ)
Captures failed messages after retry attempts for manual intervention.

### Lambda Handler
Format: `filename.function_name` (e.g., `task_lambda.lambda_handler`)

### Producer-Consumer Pattern
- **Producer**: `notifier.py` sends messages to queue
- **Consumer**: `notification_lambda.py` processes messages from queue

## 🎯 Next Steps

- [ ] Add email/SMS integration in notification_lambda
- [ ] Implement order status tracking
- [ ] Add database for order history
- [ ] Deploy to real AWS
- [ ] Add monitoring and alerting
- [ ] Implement API rate limiting

## 📄 License

This is a POC project for learning AWS services with LocalStack.

## 👥 Contributing

This is a learning project. Feel free to fork and experiment!

---

**Built with ❤️ using LocalStack and AWS Services**
