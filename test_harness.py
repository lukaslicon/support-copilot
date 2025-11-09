# Copyright Lukas Licon 2025. All Rights Reserved.

from datetime import datetime
from typing import Any, Dict, Optional
from langgraph.types import Command
from app.graph import graph
from app.state import Ticket

def _strip_fence(s: str | None) -> str:
    if not s:
        return ""
    t = s.strip()
    if t.startswith("```"):
        t = "\n".join(t.splitlines()[1:])
        if t.endswith("```"):
            t = "\n".join(t.splitlines()[:-1])
    return t.strip()

def run_once(
    *,
    label: str,
    amount_cents: int,
    order_id: Optional[str],
    text: str,
    extra_meta: Optional[Dict[str, Any]] = None,
    hil_decision: Optional[str] = None,   # "approve" | "deny" | "defer" | None
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {"amount_cents": amount_cents}
    meta["order_id"] = order_id
    if extra_meta:
        meta.update(extra_meta)

    ticket = Ticket(
        id=f"t_{label}",
        channel="email",
        created_at=datetime.utcnow(),
        customer_id="cus_demo",
        text=text,
        metadata=meta,
    )

    cfg = {"configurable": {"thread_id": f"th_{label}"}}
    initial = {"ticket": ticket}

    # 1st invoke — may produce an interrupt
    result = graph.invoke(initial, cfg)
    interrupted = bool(result.get("__interrupt__"))

    if interrupted:
        decision = hil_decision or "approve"
        result = graph.invoke(Command(resume=decision), cfg)

    draft = result.get("draft")
    md = getattr(draft, "markdown", None) if draft else None
    if md is None and isinstance(draft, dict):
        md = draft.get("markdown")
    md = _strip_fence(md)

    approvals = result.get("approvals", {})
    executed = result.get("executed") or []
    actions_run = [getattr(r, "tool", None) or (r.get("tool") if isinstance(r, dict) else None) for r in executed]

    missing = result.get("missing_requirements") or []
    plan = result.get("actions")  # may be None or ActionPlan

    first_line = (md or "").splitlines()[0] if md else "(no draft)"
    return {
        "label": label,
        "amount_cents": amount_cents,
        "order_id": order_id,
        "was_interrupted": interrupted,
        "hil_decision": hil_decision,
        "approvals": approvals,
        "executed_tools": actions_run,
        "missing_requirements": missing,
        "has_plan": bool(plan),
        "draft_preview": first_line,
    }

def print_summary(row: Dict[str, Any]):
    print(f"\n=== {row['label']} ===")
    print(f"amount: {row['amount_cents']}¢   order_id: {row['order_id']}")
    print(f"interrupted_for_HIL: {row['was_interrupted']}   decision: {row['hil_decision']}")
    print(f"approvals: {row['approvals']}")
    print(f"executed_tools: {row['executed_tools']}")
    print(f"missing_requirements: {row['missing_requirements']}")
    print(f"has_plan: {row['has_plan']}")
    print(f"draft: {row['draft_preview']}")

if __name__ == "__main__":
    tests = [
        # LOW — auto-refund (no approval)
        dict(
            label="LOW_auto_refund",
            amount_cents=1500,
            order_id="A100",
            text="I was double charged, please refund the extra $15.",
            extra_meta={"explanation":"charged twice"},
            hil_decision=None,
        ),
        # MEDIUM — HIL approve
        dict(
            label="MEDIUM_hil_approve",
            amount_cents=3500,
            order_id="A101",
            text="Charged twice—please refund the extra $35.",
            extra_meta={"explanation":"charged twice","images":["proof.png"]},
            hil_decision="approve",
        ),
        # MEDIUM — HIL deny
        dict(
            label="MEDIUM_hil_deny",
            amount_cents=3500,
            order_id="A102",
            text="Need a $35 refund.",
            extra_meta={"explanation":"charged twice","images":["proof.png"]},
            hil_decision="deny",
        ),
        # HIGH — auto-escalate/notify (no approval)
        dict(
            label="HIGH_escalate_notify",
            amount_cents=6000,
            order_id="A103",
            text="I was charged an extra $60, please refund.",
            extra_meta={"explanation":"charged twice"},
            hil_decision=None,
        ),
        # MISSING EVIDENCE — ask for info (no approval, no execute)
        dict(
            label="MISSING_EVIDENCE_request_info",
            amount_cents=2800,
            order_id=None,  # missing order id
            text="refund for double charge please",
            extra_meta={},   # no explanation, no images
            hil_decision=None,
        ),
        # POLICY BLOCK — e.g., active chargeback (auto-escalate)
        dict(
            label="POLICY_BLOCK_chargeback",
            amount_cents=1200,
            order_id="A104",
            text="refund please",
            extra_meta={"chargeback_open": True, "explanation":"charged twice"},
            hil_decision=None,
        ),
    ]

    for t in tests:
        out = run_once(**t)
        print_summary(out)

    print("\n>> All category tests finished.\n")