# Copyright Lukas Licon 2025. All Rights Reserved.

from .state import CaseState, ActionPlan, ActionStep
from .config import (
    REFUND_CAP_CENTS,
    LOW_THRESHOLD_CENTS,
    MEDIUM_THRESHOLD_CENTS,
)
from .policy import required_evidence_for, which_missing

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

def plan_actions(state: CaseState):
    """
    Returns (ActionPlan | None, missing_requirements: list[str])
    - If over cap: escalate (notify), no approval.
    - If missing required evidence: no steps (let draft request items).
    - If low & evidence met: auto refund.
    - If medium & evidence met: HIL refund.
    """
    intents = set(state.get("intents", []))
    text = state["ticket"].text if state.get("ticket") else ""
    meta = state["ticket"].metadata if state.get("ticket") else {}
    if not (("billing" in intents) or _looks_like_billing(text)):
        return None, []

    cents = max(1, meta.get("amount_cents", 0))

    # Hard policy cap → auto deny & escalate via notify
    if cents > REFUND_CAP_CENTS:
        esc = ActionStep(
            tool="notify",
            args={
                "channel": "email",
                "to": None,
                "subject": f"Escalation needed for refund request: ticket {state['ticket'].id}",
                "message": f"Requested {cents}¢ for order {meta.get('order_id','')}: over policy cap.",
            },
            guard="auto_escalate_over_cap",
            rationale="Over policy cap; deny and escalate.",
        )
        return ActionPlan(ticket_id=state["ticket"].id, steps=[esc], requires_approval=False), []

    # Evidence policy
    required = required_evidence_for(cents=cents, metadata=meta, text=text)
    missing = which_missing(required=required, metadata=meta, text=text)

    # If required items are missing → no steps yet; draft will ask for them
    if missing:
        # Return no plan (None); the graph will draft a “need info” reply.
        return None, missing

    # Evidence satisfied: tier by amount
    if cents <= LOW_THRESHOLD_CENTS:
        step = ActionStep(
            tool="refund",
            args={
                "customer_id": state["ticket"].customer_id or "unknown",
                "order_id": meta.get("order_id",""),
                "amount": cents,
                "reason": "policy auto-refund",
            },
            guard=f"amount_cents <= {REFUND_CAP_CENTS}",
            rationale=f"Auto-refund <= {LOW_THRESHOLD_CENTS}¢ with evidence present",
        )
        return ActionPlan(ticket_id=state["ticket"].id, steps=[step], requires_approval=False), []

    if cents <= MEDIUM_THRESHOLD_CENTS:
        step = ActionStep(
            tool="refund",
            args={
                "customer_id": state["ticket"].customer_id or "unknown",
                "order_id": meta.get("order_id",""),
                "amount": cents,
                "reason": "policy goodwill",
            },
            guard=f"amount_cents <= {REFUND_CAP_CENTS}",
            rationale=f"HIL {LOW_THRESHOLD_CENTS}<={cents}<={MEDIUM_THRESHOLD_CENTS} with evidence present",
        )
        return ActionPlan(ticket_id=state["ticket"].id, steps=[step], requires_approval=True), []

    # Above medium but <= cap (shouldn't happen with defaults, but keep symmetric)
    esc = ActionStep(
        tool="notify",
        args={
            "channel": "email",
            "to": None,
            "subject": f"Escalation needed for refund request: ticket {state['ticket'].id}",
            "message": f"Requested {cents}¢ for order {meta.get('order_id','')}: above medium threshold.",
        },
        guard="auto_escalate_high",
        rationale="Above medium threshold; deny and escalate.",
    )
    return ActionPlan(ticket_id=state["ticket"].id, steps=[esc], requires_approval=False), []
