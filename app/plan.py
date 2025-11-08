# Copyright Lukas Licon 2025. All Rights Reserved.

from .state import CaseState, ActionPlan, ActionStep

REFUND_CAP_USD = 50

def plan_actions(state: CaseState) -> ActionPlan | None:
    if "billing" in state["intents"]:
        # demo rule: propose a refund up to cap
        step = ActionStep(
            tool="refund",
            args={"customer_id": state["ticket"].customer_id or "unknown",
                  "order_id": state["ticket"].metadata.get("order_id",""),
                  "amount": min(REFUND_CAP_USD*100, state["ticket"].metadata.get("amount_cents", 0)),
                  "reason": "policy goodwill"},
            guard=f"amount <= ${REFUND_CAP_USD} cap",
            rationale="Within 30-day window and cap"
        )
        return ActionPlan(ticket_id=state["ticket"].id, steps=[step], requires_approval=True)
    return None