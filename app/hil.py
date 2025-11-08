# Copyright Lukas Licon 2025. All Rights Reserved.

from langgraph.types import interrupt
from .state import CaseState

def interrupt_approval(state: CaseState):
    """
    HIL with tri-state. Auto-approve only when:
      - plan.requires_approval is False AND plan contains a 'refund' step.
    Escalation-only plans should NOT mark approvals true.
    """
    plan = state.get("actions")
    if not plan:
        return {"approvals": {}}

    has_refund = any(s.tool == "refund" for s in plan.steps)

    # Auto-approve low-tier refund plans
    if (getattr(plan, "requires_approval", False) is False) and has_refund:
        return {"approvals": {"actions": True}}

    # Escalation-only plan: no approval, just proceed to draft/execute path
    if (getattr(plan, "requires_approval", False) is False) and not has_refund:
        # leave approvals unset/False; execute_node will handle escalation
        return {"approvals": {}}

    # Await human for medium-tier refund plans
    if "approved" in state:
        return {"approvals": {"actions": bool(state["approved"])}}

    decision = interrupt({"plan": plan})  # "approve" | "deny" | "defer"
    if decision == "approve":
        return {"approvals": {"actions": True}}
    if decision == "deny":
        return {"approvals": {"actions": False}}
    # defer/pending
    return {"approvals": {}}
