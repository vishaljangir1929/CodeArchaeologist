from __future__ import annotations

from .models import CartItem, Product
from .service import CheckoutService


def build_demo_cart() -> list[CartItem]:
    keyboard = Product(sku="KB-01", name="Mechanical Keyboard", price=3200.0)
    mouse = Product(sku="MS-04", name="Wireless Mouse", price=900.0)
    return [CartItem(keyboard, 1), CartItem(mouse, 2)]


def main() -> None:
    service = CheckoutService()
    order = service.checkout("student@example.com", build_demo_cart(), previous_orders=6)
    print(f"Order total: {order.total}")


if __name__ == "__main__":
    main()

