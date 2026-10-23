from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Product:
    sku: str
    name: str
    price: float


@dataclass
class CartItem:
    product: Product
    quantity: int

    def subtotal(self) -> float:
        return self.product.price * self.quantity


@dataclass
class Order:
    customer_email: str
    items: list[CartItem]
    total: float


def calculate_total(items: list[CartItem]) -> float:
    total = 0.0
    for item in items:
        total += item.subtotal()
    return round(total, 2)


def normalize_sku(raw_sku: str) -> str:
    return raw_sku.strip().upper().replace(" ", "-")

