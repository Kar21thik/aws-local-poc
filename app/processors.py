# app/processors.py
import time
import logging

logger = logging.getLogger(__name__)

def validate_order(items):
    """Check if order is valid"""
    if not items or len(items) == 0:
        return False
    
    for item in items:
        if item.get('quantity', 0) <= 0 or item.get('price', 0) <= 0:
            return False
    
    return True

def calculate_order_total(items):
    """Calculate total from items list"""
    total = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
    return round(total, 2)

def apply_discount(subtotal, promo_code):
    """Apply discount based on promo code"""
    discounts = {"SAVE10": 0.10, "SAVE20": 0.20, "SAVE30": 0.30, "FREESHIP": 0.05}
    discount_rate = discounts.get(promo_code, 0)
    discount_amount = subtotal * discount_rate
    final_total = subtotal - discount_amount
    return round(final_total, 2), round(discount_amount, 2)

def build_invoice(order_id, items, subtotal, discount_amount, final_total, promo_code):
    """Create invoice object"""
    return {
        "order_id": order_id,
        "items": items,
        "item_count": len(items),
        "subtotal": subtotal,
        "promo_code": promo_code if promo_code else "None",
        "discount": discount_amount,
        "final_total": final_total,
        "status": "completed",
        "timestamp": time.time()
    }
