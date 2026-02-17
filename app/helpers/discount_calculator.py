"""
Discount calculator - nested inside app/helpers/
"""
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info("📦 MODULE LOADED: app/helpers/discount_calculator.py")

def calculate_bulk_discount(subtotal):
    """Apply bulk discount based on order size"""
    logger.info(f"   🔹 Accessing: calculate_bulk_discount() from app/helpers/")
    logger.info(f"   🔹 Input: subtotal=${subtotal:.2f}")
    
    if subtotal > 1000:
        discount = subtotal * 0.15  # 15% off
        logger.info(f"   🔹 Applied: 15% bulk discount")
        return discount
    elif subtotal > 500:
        discount = subtotal * 0.10  # 10% off
        logger.info(f"   🔹 Applied: 10% bulk discount")
        return discount
    elif subtotal > 100:
        discount = subtotal * 0.05  # 5% off
        logger.info(f"   🔹 Applied: 5% bulk discount")
        return discount
    
    logger.info(f"   🔹 Applied: No bulk discount (subtotal too low)")
    return 0

def calculate_tax(amount):
    """Calculate tax"""
    logger.info(f"   🔹 Accessing: calculate_tax() from app/helpers/")
    logger.info(f"   🔹 Input: amount=${amount:.2f}")
    tax = amount * 0.08  # 8% tax
    logger.info(f"   🔹 Calculated: 8% tax = ${tax:.2f}")
    return tax
