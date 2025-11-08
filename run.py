# Copyright Lukas Licon 2025. All Rights Reserved.

from datetime import datetime
from typing import Any, Dict
from langgraph.types import Command
from app.graph import graph
from app.state import Ticket

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
    ticket = Ticket(
        id="t_demo_1",
        channel="email",
        created_at=datetime.utcnow(),
        customer_id="cus_123",
        text="I was double charged for order #A100, please refund the extra $25.",
        metadata={"order_id": "A100", "amount_cents": 2500},
    )

    cfg = {"configurable": {"thread_id": "demo-thread"}}
    initial = {"ticket": ticket}

    print(">> Running until approval (will pause if a plan exists)...")
    result = graph.invoke(initial, cfg)

    interrupts = result.get("__interrupt__")
    if interrupts:
        payload = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
        plan = payload.get("plan") if isinstance(payload, dict) else payload
        print("Approval requested. Proposed plan:\n")
        print(plan)

        # 3-way decision
        choice = input("\nApprove, Deny, or Defer? [a/d/Enter=defer]: ").strip().lower()
        if choice.startswith("a"):
            resume_value = "approve"
        elif choice.startswith("d"):
            resume_value = "deny"
        else:
            resume_value = "defer"

        print("\n>> Resuming with your decision...\n")
        final_state = graph.invoke(Command(resume=resume_value), cfg)
        _print_outputs(final_state)
        print("\n>> Done.")
    else:
        print("No approval needed. Running to completion...\n")
        _print_outputs(result)
        print("\n>> Done.")