# Copyright Lukas Licon 2025. All Rights Reserved.
from langchain.tools import tool
from pydantic import BaseModel, Field

class RefundInput(BaseModel):
    customer_id: str
    order_id: str
    amount: int = Field(ge=1, le=50000)  # cents
    reason: str

@tool("refund", args_schema=RefundInput)
def refund_tool(customer_id: str, order_id: str, amount: int, reason: str):
    """Issue a refund (in cents) for a given order and customer.

    This tool expects:
      - customer_id: external customer identifier
      - order_id: the order to refund
      - amount: integer amount in **cents** (validated 1..50000 here)
      - reason: short free-text justification (stored for audit)

    Returns a JSON receipt with refund_id, currency, and amount.
    In production, wire this to your payment provider (e.g., Stripe sandbox)
    and add idempotency using a stable key like f"{order_id}:{amount}".
    """
    # TODO: policy checks, idempotency key, payment API call
    return {"refund_id": "rf_123", "currency": "USD", "amount": amount}
