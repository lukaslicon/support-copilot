# Copyright Lukas Licon 2025. All Rights Reserved.

from datetime import datetime
import argparse
from typing import Any, Dict, Optional
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

def parse_args():
    p = argparse.ArgumentParser(description="Support Copilot runner")
    p.add_argument("--amount-cents", type=int, default=2500, help="Refund amount in cents (e.g., 1000=$10)")
    p.add_argument("--order-id", default="A100")
    p.add_argument("--customer-id", default="cus_123")
    p.add_argument("--text", default="I was double charged, please refund the extra amount.")
    p.add_argument(
        "--decision",
        choices=["approve", "deny", "defer"],
        help="Auto decision for HIL; if omitted, you'll be prompted when required.",
    )
    p.add_argument("--thread", default="demo-thread")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()

    ticket = Ticket(
        id=f"t_{args.amount_cents}",
        channel="email",
        created_at=datetime.utcnow(),
        customer_id=args.customer_id,
        text=args.text,
        metadata={"order_id": args.order_id, "amount_cents": args.amount_cents},
    )

    cfg = {"configurable": {"thread_id": args.thread}}
    initial = {"ticket": ticket}

    print(">> Running (will pause if a plan needs approval)...")
    result = graph.invoke(initial, cfg)

    interrupts = result.get("__interrupt__")
    if interrupts:
        payload = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
        plan = payload.get("plan") if isinstance(payload, dict) else payload
        print("Approval requested. Proposed plan:\n")
        print(plan)

        if args.decision:
            resume_value = args.decision
            print(f"\n>> Auto-deciding: {resume_value}\n")
        else:
            choice = input("\nApprove, Deny, or Defer? [a/d/Enter=defer]: ").strip().lower()
            if choice.startswith("a"):
                resume_value = "approve"
            elif choice.startswith("d"):
                resume_value = "deny"
            else:
                resume_value = "defer"

        final_state = graph.invoke(Command(resume=resume_value), cfg)
        _print_outputs(final_state)
        print("\n>> Done.")
    else:
        print("No approval needed. Running to completion...\n")
        _print_outputs(result)
        print("\n>> Done.")
