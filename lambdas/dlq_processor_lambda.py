import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from app.processors import calculate_order_total, apply_discount, build_invoice
from app.storage import save_to_s3
from app.notifier import send_notification

BUCKET = "results-bucket"
QUEUE_NAME = "notification-queue"

endpoint = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566").rstrip("/")
NOTIFICATION_QUEUE_URL = f"{endpoint}/000000000000/{QUEUE_NAME}"
TASK_QUEUE_URL = f"{endpoint}/000000000000/task-queue"

def fix_order_data(body):
    """Attempt to fix common order issues"""
    fixed = False
    issues = []
    
    # Fix negative prices
    if "items" in body:
        for item in body["items"]:
            if item.get("price", 0) < 0:
                item["price"] = abs(item["price"])
                fixed = True
                issues.append(f"Fixed negative price for {item['name']}")
            
            if item.get("quantity", 0) <= 0:
                item["quantity"] = 1
                fixed = True
                issues.append(f"Fixed invalid quantity for {item['name']}")
    
    # Check if items exist
    if not body.get("items") or len(body["items"]) == 0:
        issues.append("Cannot fix: No items in order")
        return None, issues
    
    return body if fixed else None, issues

def lambda_handler(event, context):
    logger.info("\n" + "="*70)
    logger.info("🔄 DLQ PROCESSOR LAMBDA INVOKED")
    logger.info("="*70)
    
    for record in event.get("Records", []):
        order_id = "Unknown"
        correlation_id = "N/A"
        
        try:
            body = json.loads(record["body"])
            order_id = body.get("order_id", "Unknown")
            correlation_id = body.get("correlation_id", "N/A")
            
            logger.info(f"\n⚠️ PROCESSING FAILED ORDER: {order_id} | Correlation: {correlation_id}")
            
            # Attempt to fix the order
            fixed_body, issues = fix_order_data(body)
            
            if issues:
                logger.info(f"   Issues found: {', '.join(issues)}")
            
            if fixed_body is None:
                logger.error(f"   ❌ Cannot auto-fix order {order_id} - requires manual intervention")
                logger.info("="*70 + "\n")
                continue
            
            # If fixed, reprocess the order
            logger.info(f"   ✅ Order fixed, reprocessing...")
            
            items = fixed_body.get("items", [])
            promo_code = fixed_body.get("promo_code", "")
            
            # Calculate
            logger.info(f"\n→ Step 1: calculate_order_total()")
            subtotal = calculate_order_total(items)
            logger.info(f"   Subtotal: ${subtotal}")
            
            logger.info(f"\n→ Step 2: apply_discount()")
            final_total, discount_amount = apply_discount(subtotal, promo_code)
            logger.info(f"   Discount: ${discount_amount} | Final: ${final_total}")
            
            # Build invoice
            logger.info(f"\n→ Step 3: build_invoice()")
            invoice = build_invoice(order_id, items, subtotal, discount_amount, final_total, promo_code)
            invoice["correlation_id"] = correlation_id
            invoice["recovered_from_dlq"] = True
            invoice["dlq_fixes"] = issues
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
                "status": "recovered_from_dlq",
                "final_total": final_total,
                "invoice_location": f"s3://{BUCKET}/{key}",
                "fixes_applied": issues
            })
            
            logger.info(f"\n✅ ORDER {order_id} RECOVERED AND COMPLETED")
            logger.info("="*70 + "\n")
            
        except Exception as e:
            logger.error(f"\n❌ ERROR processing DLQ message for {order_id}: {str(e)}")
            logger.info("="*70 + "\n")

    return {"status": "dlq_processed"}
