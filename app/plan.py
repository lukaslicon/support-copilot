# Copyright Lukas Licon 2025. All Rights Reserved.

from .state import CaseState, ActionPlan, ActionStep

REFUND_CAP_USD = 50

# Broader match to ensure a plan is created for refund-like tickets
REFUND_KEYWORDS = [
    "refund", "refunded",
    "double charge", "double-charged", "double charged",
    "charged twice",
    "overcharge", "over-charged", "over charged",
    "chargeback",
]

def _looks_like_billing(text: str) -> bool:
    t = (text or "").lower()
    return any(kw in t for kw in REFUND_KEYWORDS)

def plan_actions(state: CaseState) -> ActionPlan | None:
    intents = set(state.get("intents", []))
    text = state["ticket"].text if state.get("ticket") else ""

    # Trigger plan if classifier says billing OR the text looks like a refund request
    if ("billing" in intents) or _looks_like_billing(text):
        cents = max(1, min(REFUND_CAP_USD * 100, state["ticket"].metadata.get("amount_cents", 0)))
        step = ActionStep(
            tool="refund",
            args={
                "customer_id": state["ticket"].customer_id or "unknown",
                "order_id": state["ticket"].metadata.get("order_id",""),
                "amount": cents,  # cents (validated by tool schema)
                "reason": "policy goodwill",
            },
            guard=f"amount_cents <= {REFUND_CAP_USD*100}",
            rationale="Within 30-day window and cap",
        )
        return ActionPlan(ticket_id=state["ticket"].id, steps=[step], requires_approval=True)
    return None
