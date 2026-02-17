import json
from datetime import datetime
from app.config import get_aws_client
from app.parameter_store import get_cached_parameter

def save_order(order_id, status, subtotal, discount_amount, final_total, items, promo_code="", recovered=False):
    """Save order to DynamoDB"""
    dynamodb = get_aws_client("dynamodb")
    table_name = get_cached_parameter("poc-orders-table-name")
    
    dynamodb.put_item(
        TableName=table_name,
        Item={
            "order_id": {"S": order_id},
            "status": {"S": status},
            "timestamp": {"S": datetime.utcnow().isoformat()},
            "subtotal": {"N": str(subtotal)},
            "discount_amount": {"N": str(discount_amount)},
            "final_total": {"N": str(final_total)},
            "promo_code": {"S": promo_code},
            "items_json": {"S": json.dumps(items)},
            "recovered_from_dlq": {"BOOL": recovered}
        }
    )

def update_order_status(order_id, status, recovered=False):
    """Update order status in DynamoDB"""
    dynamodb = get_aws_client("dynamodb")
    table_name = get_cached_parameter("poc-orders-table-name")
    
    dynamodb.update_item(
        TableName=table_name,
        Key={"order_id": {"S": order_id}},
        UpdateExpression="SET #status = :status, recovered_from_dlq = :recovered",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":status": {"S": status},
            ":recovered": {"BOOL": recovered}
        }
    )
