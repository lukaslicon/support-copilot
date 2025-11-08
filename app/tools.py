# Copyright Lukas Licon 2025. All Rights Reserved.

from typing import Optional
from pydantic import BaseModel, Field
from .config import SUPPORT_ESCALATION_EMAIL

class RefundArgs(BaseModel):
    customer_id: str = Field(..., description="Customer identifier")
    order_id: str = Field(..., description="Order ID to refund against")
    amount: int = Field(..., ge=1, le=50000, description="Refund amount in cents (1..50000)")
    reason: str = Field(..., description="Refund reason")

class NotifyArgs(BaseModel):
    channel: str = Field(..., description="notification channel, e.g. 'email'")
    to: Optional[str] = Field(None, description="Recipient; defaults to SUPPORT_ESCALATION_EMAIL")
    subject: str
    message: str

def refund_tool(args: RefundArgs) -> dict:
    return {"refund_id": "rf_123", "currency": "USD", "amount": args.amount}

def notify_tool(args: NotifyArgs) -> dict:
    if args.channel != "email":
        # mock non-email channels if you add them later
        return {"queued": True, "channel": args.channel}
    to = args.to or SUPPORT_ESCALATION_EMAIL
    if "@" not in to or "." not in to:  # light sanity check
        to = SUPPORT_ESCALATION_EMAIL
    return {"queued": True, "channel": "email", "to": to, "subject": args.subject}

TOOLS = {
    "refund": (RefundArgs, refund_tool),
    "notify": (NotifyArgs, notify_tool),
}
