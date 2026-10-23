from __future__ import annotations

from .discounts import loyalty_discount, seasonal_discount
from .models import CartItem, Order, calculate_total
from .notifications import send_receipt


class CheckoutService:
    def checkout(self, email: str, items: list[CartItem], previous_orders: int = 0) -> Order:
        self.validate_cart(items)
        total = calculate_total(items)
        total -= seasonal_discount(total)
        total -= loyalty_discount(total, previous_orders)
        order = Order(customer_email=email, items=items, total=round(total, 2))
        send_receipt(order)
        return order

    def validate_cart(self, items: list[CartItem]) -> None:
        if not items:
            raise ValueError("cart is empty")
        for item in items:
            if item.quantity <= 0:
                raise ValueError("quantity must be positive")
            if item.product.price < 0:
                raise ValueError("price cannot be negative")


class DebugCheckoutPrinter:
    def print_order(self, order: Order) -> None:
        print(order)

