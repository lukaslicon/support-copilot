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
    p.add_argument("--order-id", default="A100", help="Order ID string; use '' or --no-order-id to omit")
    p.add_argument("--no-order-id", action="store_true", help="Simulate missing order id")
    p.add_argument("--customer-id", default="cus_123")
    p.add_argument("--text", default="I was double charged, please refund the extra amount.")
    p.add_argument("--decision", choices=["approve", "deny", "defer"], help="Auto decision for HIL when required")
    p.add_argument("--thread", default="demo-thread")

    # Evidence knobs
    p.add_argument("--explanation", default=None, help="Short explanation string")
    p.add_argument("--image", action="append", default=None, help="Add an image path/URL; repeat flag to add multiple")
    p.add_argument("--return-status", choices=["initiated","received",""], default="", help="Return status")
    p.add_argument("--physical-item", action="store_true", help="Mark item as physical (may require return/photo)")
    p.add_argument("--evidence-required", action="store_true", help="Force requiring photo evidence")

    # Power users: pass raw JSON for metadata (merges with flags above; flags win)
    p.add_argument("--meta", default=None, help='JSON blob to merge into metadata, e.g. {"gift_card": true}')
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Build metadata
    md: Dict[str, Any] = {"amount_cents": args.amount_cents}
    if args.meta:
        try:
            md.update(json.loads(args.meta))
        except Exception:
            print("Warning: --meta is not valid JSON; ignoring.")

    # order_id handling (allow empty)
    if args.no_order_id or args.order_id == "":
        md["order_id"] = None
    else:
        md["order_id"] = args.order_id

    # evidence fields
    if args.explanation is not None:
        md["explanation"] = args.explanation
    if args.image:
        md["images"] = args.image
    if args.return_status != "":
        md["return_status"] = args.return_status
    if args.physical_item:
        md["physical_item"] = True
    if args.evidence_required:
        md["evidence_required"] = True

    ticket = Ticket(
        id=f"t_{args.amount_cents}",
        channel="email",
        created_at=datetime.utcnow(),
        customer_id=args.customer_id,
        text=args.text,
        metadata=md,
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
            if choice.startswith("a"): resume_value = "approve"
            elif choice.startswith("d"): resume_value = "deny"
            else: resume_value = "defer"

        final_state = graph.invoke(Command(resume=resume_value), cfg)
        _print_outputs(final_state)
        print("\n>> Done.")
    else:
        print("No approval needed. Running to completion...\n")
        _print_outputs(result)
        print("\n>> Done.")
