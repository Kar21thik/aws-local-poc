"""
Discount calculator - nested inside app/helpers/
"""

def calculate_bulk_discount(subtotal):
    """Apply bulk discount based on order size"""
    if subtotal > 1000:
        return subtotal * 0.15  # 15% off
    elif subtotal > 500:
        return subtotal * 0.10  # 10% off
    elif subtotal > 100:
        return subtotal * 0.05  # 5% off
    return 0

def calculate_tax(amount):
    """Calculate tax"""
    return amount * 0.08  # 8% tax
