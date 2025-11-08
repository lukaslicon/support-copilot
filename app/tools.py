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
    # TODO: policy checks, idempotency key, Stripe sandbox call
    return {"refund_id":"rf_123", "currency":"USD", "amount": amount}