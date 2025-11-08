# Copyright Lukas Licon 2025. All Rights Reserved.

from langgraph.types import interrupt
from .state import CaseState

def interrupt_approval(state: CaseState):
    # This pauses the graph. The JSON you pass here is shown to the human.
    decision = interrupt({"type": "APPROVAL_NEEDED", "plan": state["actions"]})
    # When resumed, this function returns with 'decision' populated.
    return {"approvals": {"actions": bool(decision.get("approved", False))}}