from __future__ import annotations

from .models import Order


def format_receipt(order: Order) -> str:
    lines = [f"Receipt for {order.customer_email}", ""]
    for item in order.items:
        lines.append(f"{item.product.name} x {item.quantity}: {item.subtotal():.2f}")
    lines.append("")
    lines.append(f"Total: {order.total:.2f}")
    return "\n".join(lines)


def send_receipt(order: Order) -> str:
    receipt = format_receipt(order)
    return f"queued:{hash(receipt)}"

