# Copyright Lukas Licon 2025. All Rights Reserved.
# app/hil.py
from langgraph.types import interrupt
from .state import CaseState

def interrupt_approval(state: CaseState):
    plan = state["actions"]
    if not plan:
        # Nothing to approve; proceed without an approval stop.
        return {"approvals": {"actions": False}}
    # This pauses the graph. The JSON you pass here is shown to the human.
    decision = interrupt({"type": "APPROVAL_NEEDED", "plan": plan})
    # When resumed, this function returns with 'decision' populated.
    return {"approvals": {"actions": bool(decision.get("approved", False))}}
