# run.py — robust runner for Support Actions Copilot (with/without approval)

from datetime import datetime
from typing import Any, Dict, Tuple

from app.graph import graph
from app.state import Ticket

def _extract_plan_from_interrupt(event: Any):
    """
    Accepts common shapes from LangGraph stream:
      tuple: ("approval", {"value": {"plan": ...}}) or ("approval", {"plan": ...})
      dict : {"approval": {"value": {"plan": ...}}} or {"value": {"plan": ...}}
    Returns (node_name, plan_obj) or (None, None).
    """
    # tuple case
    if isinstance(event, tuple) and len(event) == 2:
        node, payload = event
        if isinstance(payload, dict):
            plan = payload.get("value", {}).get("plan") or payload.get("plan") or payload.get("actions")
            return node, plan

    # dict with node key
    if isinstance(event, dict):
        if "approval" in event and isinstance(event["approval"], dict):
            payload = event["approval"]
            plan = payload.get("value", {}).get("plan") or payload.get("plan") or payload.get("actions")
            return "approval", plan
        if "value" in event and isinstance(event["value"], dict):
            plan = event["value"].get("plan") or event["value"].get("actions")
            return None, plan

    return None, None

def _print_outputs(state: Dict[str, Any]):
    draft = state.get("draft")
    if draft:
        print("=== Draft Reply ===")
        md = getattr(draft, "markdown", None)
        if md is None and isinstance(draft, dict):
            md = draft.get("markdown")
        print(md or draft)

    executed = state.get("executed")
    if executed:
        print("\n=== Execution Results ===")
        print(executed)

    artifacts = state.get("artifacts")
    if artifacts:
        print("\n=== Artifacts ===")
        print(artifacts)

if __name__ == "__main__":
    # Seed ticket
    ticket = Ticket(
        id="t_demo_1",
        channel="email",
        created_at=datetime.utcnow(),
        customer_id="cus_123",
        text="I was double charged for order #A100, please refund the extra $25.",
        metadata={"order_id": "A100", "amount_cents": 2500},
    )

    initial = {"ticket": ticket}
    cfg = {"configurable": {"thread_id": "demo-thread"}}

    print(">> Running until approval...")

    interrupt_event: Any = None
    for event in graph.stream(initial, cfg):
        node, plan = _extract_plan_from_interrupt(event)
        if node == "approval" or plan is not None:
            interrupt_event = event
            break

    if interrupt_event:
        # We hit approval
        _, plan = _extract_plan_from_interrupt(interrupt_event)
        print("Approval requested. Proposed plan:\n", plan)

        print("\n>> Resuming with approval...\n")
        final_state = graph.invoke({"approved": True}, cfg)
        _print_outputs(final_state)
        print("\n>> Done.")
    else:
        # No approval needed this run — finish and print results
        print("No approval needed. Running to completion...\n")
        final_state = graph.invoke(initial, cfg)
        _print_outputs(final_state)
        print("\n>> Done.")
