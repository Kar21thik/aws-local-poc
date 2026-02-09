# notification_lambda.py
import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("\n" + "="*70)
    logger.info("🔔 NOTIFICATION LAMBDA INVOKED")
    logger.info("="*70)

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            order_id = body.get("order_id", "Unknown")
            correlation_id = body.get("correlation_id", "N/A")
            status = body.get("status", "Unknown")
            final_total = body.get("final_total", 0)
            
            logger.info(f"\n📧 NOTIFICATION RECEIVED:")
            logger.info(f"   Order: {order_id} | Correlation: {correlation_id}")
            logger.info(f"   Status: {status}")
            logger.info(f"   Total: ${final_total}")
            logger.info(f"\n✅ Notification processed")
            logger.info("="*70 + "\n")
            
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            logger.info("="*70 + "\n")

    return {"status": "notified"}
