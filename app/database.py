"""
DynamoDB operations for order tracking
"""

import os
import time
from decimal import Decimal
from app.config import get_aws_client

ORDERS_TABLE = os.environ.get("ORDERS_TABLE", "orders-dev")

def save_order_status(order_id, status, user_id=None, items=None, total=None, metadata=None):
    """
    Save or update order status in DynamoDB
    """
    dynamodb = get_aws_client("dynamodb")
    
    item = {
        "order_id": {"S": order_id},
        "status": {"S": status},
        "updated_at": {"N": str(int(time.time()))}
    }
    
    if user_id:
        item["user_id"] = {"S": user_id}
        item["created_at"] = {"N": str(int(time.time()))}
    
    if items:
        item["item_count"] = {"N": str(len(items))}
    
    if total:
        item["total"] = {"N": str(Decimal(str(total)))}
    
    if metadata:
        item["metadata"] = {"S": str(metadata)}
    
    dynamodb.put_item(
        TableName=ORDERS_TABLE,
        Item=item
    )

def get_order(order_id):
    """
    Retrieve order from DynamoDB
    """
    dynamodb = get_aws_client("dynamodb")
    
    response = dynamodb.get_item(
        TableName=ORDERS_TABLE,
        Key={"order_id": {"S": order_id}}
    )
    
    return response.get("Item")

def get_user_orders(user_id, limit=20):
    """
    Get all orders for a user
    """
    dynamodb = get_aws_client("dynamodb")
    
    response = dynamodb.query(
        TableName=ORDERS_TABLE,
        IndexName="user-orders-index",
        KeyConditionExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": {"S": user_id}},
        Limit=limit,
        ScanIndexForward=False  # Most recent first
    )
    
    return response.get("Items", [])
