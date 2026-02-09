# used the dataclass here , Pydantic was creating some errors while running in the localstack.
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Item:
    name: str
    price: float
    quantity: int
    
    def validate(self):
        if not self.name or not self.name.strip():
            raise ValueError("Item name is required")
        # Allow negative prices to test DLQ - Lambda will catch it
        if self.quantity <= 0:
            raise ValueError("Item quantity must be positive")

@dataclass
class Order:
    items: List[dict]
    promo_code: Optional[str] = None
    
    def validate(self):
        if not self.items:
            raise ValueError("Order must have at least one item")
        for item_data in self.items:
            item = Item(**item_data)
            item.validate()
