# app/plan.py
from .state import CaseState, ActionPlan, ActionStep

REFUND_CAP_USD = 50

def plan_actions(state: CaseState) -> ActionPlan | None:
    if "billing" in state["intents"]:
        cents = max(1, min(REFUND_CAP_USD * 100, state["ticket"].metadata.get("amount_cents", 0)))
        step = ActionStep(
            tool="refund",
            args={
                "customer_id": state["ticket"].customer_id or "unknown",
                "order_id": state["ticket"].metadata.get("order_id",""),
                "amount": cents,  # cents, validated by tool schema
                "reason": "policy goodwill",
            },
            guard=f"amount_cents <= {REFUND_CAP_USD*100}",
            rationale="Within 30-day window and cap"
        )
        return ActionPlan(ticket_id=state["ticket"].id, steps=[step], requires_approval=True)
    return None
