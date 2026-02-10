# task_lambda.py
import json
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import functions
from app.processors import calculate_order_total, apply_discount, build_invoice
from app.storage import save_to_s3
from app.notifier import send_notification
from app.helpers.discount_calculator import calculate_bulk_discount, calculate_tax


BUCKET = "results-bucket"
QUEUE_NAME = "notification-queue"

# Construct SQS URL dynamically
endpoint = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566").rstrip("/")
NOTIFICATION_QUEUE_URL = f"{endpoint}/000000000000/{QUEUE_NAME}"

def lambda_handler(event, context):
    logger.info("\n" + "="*70)
    logger.info("🚀 TASK LAMBDA INVOKED")
    logger.info("="*70)
    
    for record in event.get("Records", []):
        order_id = "Unknown"
        correlation_id = "N/A"
        try:
            body = json.loads(record["body"])
            order_id = body.get("order_id")
            correlation_id = body.get("correlation_id", "N/A")
            items = body.get("items", [])
            promo_code = body.get("promo_code", "")
            
            logger.info(f"\n📦 ORDER: {order_id} | Correlation: {correlation_id}")
            logger.info(f"   Items: {len(items)} | Promo: {promo_code or 'None'}")
            
            # Validate items (reject negative values - DLQ will fix them)
            for item in items:
                if item.get("price", 0) < 0 or item.get("quantity", 0) <= 0:
                    raise ValueError(f"Invalid item: {item['name']} has negative price or invalid quantity")
            
            # Calculate
            logger.info(f"\n→ Step 1: calculate_order_total()")
            subtotal = calculate_order_total(items)
            logger.info(f"   Subtotal: ${subtotal}")
            
            logger.info(f"\n→ Step 2: apply_discount()")
            final_total, discount_amount = apply_discount(subtotal, promo_code)
            logger.info(f"   Discount: ${discount_amount} | Final: ${final_total}")
            
            # TEST: Use nested folder function
            logger.info(f"\n→ Step 2.5: calculate_bulk_discount() [NESTED FOLDER TEST]")
            bulk_discount = calculate_bulk_discount(subtotal)
            tax = calculate_tax(final_total)
            logger.info(f"   🧪 Bulk Discount: ${bulk_discount:.2f}")
            logger.info(f"   🧪 Tax: ${tax:.2f}")
            logger.info(f"   ✅ NESTED IMPORT WORKS!")
            
            # Build invoice
            logger.info(f"\n→ Step 3: build_invoice()")
            invoice = build_invoice(order_id, items, subtotal, discount_amount, final_total, promo_code)
            invoice["correlation_id"] = correlation_id
            invoice["bulk_discount"] = bulk_discount
            invoice["tax"] = tax
            logger.info(f"   ✅ Invoice created")

            # Save to S3
            logger.info(f"\n→ Step 4: save_to_s3()")
            key = f"{order_id}.json"
            save_to_s3(BUCKET, key, invoice)

            # Send notification
            logger.info(f"\n→ Step 5: send_notification()")
            send_notification(NOTIFICATION_QUEUE_URL, {
                "order_id": order_id,
                "correlation_id": correlation_id,
                "status": "processed",
                "final_total": final_total,
                "invoice_location": f"s3://{BUCKET}/{key}"
            })
            
            logger.info(f"\n✅ ORDER {order_id} COMPLETED")
            logger.info("="*70 + "\n")
            
        except Exception as e:
            logger.error(f"\n❌ ERROR processing {order_id}: {str(e)}")
            logger.error(f"   Order will be retried or moved to DLQ")
            logger.info("="*70 + "\n")
            raise  # Re-raise to trigger retry/DLQ

    return {"status": "success"}


