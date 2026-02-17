import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from app.processors import calculate_order_total, apply_discount, build_invoice
from app.storage import save_to_s3
from app.notifier import send_notification
from app.parameter_store import get_cached_parameter
from app.database import save_order, update_order_status
from app.database import update_order_status

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
    
    # Get values from Parameter Store
    BUCKET = get_cached_parameter("poc-results-bucket-name")
    NOTIFICATION_QUEUE_URL = get_cached_parameter("poc-notification-queue-url")
    
    # Track DLQ statistics
    total_messages = len(event.get("Records", []))
    processed_count = 0
    recovered_count = 0
    failed_count = 0
    
    logger.info(f"\n📊 DLQ BATCH INFO:")
    logger.info(f"   Total messages received: {total_messages}")
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

            # Save to DynamoDB with RECOVERED status
            logger.info(f"\n→ Step 5: save_order() to DynamoDB")
            save_order(
                order_id=order_id,
                status="RECOVERED",
                subtotal=subtotal,
                discount_amount=discount_amount,
                final_total=final_total,
                items=items,
                promo_code=promo_code,
                recovered=True
            )
            logger.info(f"   ✅ Order saved to DynamoDB with RECOVERED status")

            # Send notification
            logger.info(f"\n→ Step 6: send_notification()")
            send_notification(NOTIFICATION_QUEUE_URL, {
                "order_id": order_id,
                "correlation_id": correlation_id,
                "status": "recovered_from_dlq",
                "final_total": final_total,
                "invoice_location": f"s3://{BUCKET}/{key}",
                "fixes_applied": issues
            })
            
            # Update DynamoDB status
            logger.info(f"\n→ Step 6: update_order_status() in DynamoDB")
            update_order_status(order_id, status="RECOVERED", recovered=True)
            logger.info(f"   ✅ Order status updated to RECOVERED")
            
            logger.info(f"\n✅ ORDER {order_id} RECOVERED AND COMPLETED")
            logger.info("="*70 + "\n")
            processed_count += 1
            recovered_count += 1
            
        except Exception as e:
            logger.error(f"\n❌ ERROR processing DLQ message for {order_id}: {str(e)}")
            logger.info("="*70 + "\n")
            processed_count += 1
            failed_count += 1

    # Final DLQ Summary
    logger.info("\n" + "="*70)
    logger.info("📈 DLQ PROCESSING SUMMARY")
    logger.info("="*70)
    logger.info(f"   Total messages in batch: {total_messages}")
    logger.info(f"   ✅ Successfully recovered: {recovered_count}")
    logger.info(f"   ❌ Failed to recover: {failed_count}")
    logger.info(f"   📊 Success rate: {(recovered_count/total_messages*100):.1f}%" if total_messages > 0 else "   📊 Success rate: N/A")
    logger.info("="*70 + "\n")

    return {
        "status": "dlq_processed",
        "total_messages": total_messages,
        "recovered": recovered_count,
        "failed": failed_count
    }
