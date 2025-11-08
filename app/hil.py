# Copyright Lukas Licon 2025. All Rights Reserved.

from langgraph.types import interrupt
from .state import CaseState

def interrupt_approval(state: CaseState):
    """
    Human-in-the-loop approval node using LangGraph interrupts.

    Flow:
      - If there's no plan, nothing to approve -> continue.
      - If we already have a decision in state["approved"], write it to approvals.
      - Otherwise, pause here with `interrupt(...)`. The returned value on resume
        becomes the approval decision (truthy -> approve).
    """
    plan = state.get("actions")
    if not plan:
        return {"approvals": {}}  # nothing to approve

    # If runner provided a decision, commit it to state for execute_node
    if "approved" in state:
        return {"approvals": {"actions": bool(state["approved"])}}

    # Pause graph execution and surface the plan to the runner
    # This returns when graph.resume/graph.invoke(Command(resume=...)) is called
    decision = interrupt({"plan": plan})
    return {"approvals": {"actions": bool(decision)}}