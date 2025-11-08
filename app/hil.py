# Copyright Lukas Licon 2025. All Rights Reserved.

from langgraph.types import interrupt
from .state import CaseState

def interrupt_approval(state: CaseState):
    """
    Human-in-the-loop approval with tri-state:
      approved=True  -> approved
      approved=False -> denied
      no 'approved'  -> pending/deferred

    Also auto-approve when the plan does not require approval.
    """
    plan = state.get("actions")
    if not plan:
        return {"approvals": {}}  # nothing to approve

    # Auto-approve small refunds
    if hasattr(plan, "requires_approval") and not plan.requires_approval:
        return {"approved": True, "approvals": {"actions": True}}

    # Runner already decided (on resume)
    if "approved" in state:  # True or False
        return {
            "approved": bool(state["approved"]),
            "approvals": {"actions": bool(state["approved"])},
        }

    # Pause and ask the runner. Runner returns "approve" | "deny" | "defer".
    decision = interrupt({"plan": plan})

    if decision == "approve":
        return {"approved": True, "approvals": {"actions": True}}
    if decision == "deny":
        return {"approved": False, "approvals": {"actions": False}}

    # "defer" (or anything else) -> pending: leave 'approved' absent and don't set actions
    return {"approvals": {}}

