# Copyright Lukas Licon 2025. All Rights Reserved.

import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import CaseState, DraftReply
from .config import OPENAI_CHAT_MODEL

def get_llm():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0, api_key=key)

def _format_snippets(retrieved: List[dict]) -> str:
    if not retrieved:
        return "(no snippets)"
    lines = []
    for i, c in enumerate(retrieved, start=1):
        text = c.get("text", "")
        src = c.get("source") or c.get("url") or c.get("doc_id") or ""
        if src:
            lines.append(f"[{i}] {text}\n({src})")
        else:
            lines.append(f"[{i}] {text}")
    return "\n\n".join(lines)

def _has_escalation(plan) -> bool:
    try:
        return any(step.tool == "notify" for step in plan.steps)
    except Exception:
        return False

def _humanize_requirements(reqs: List[str]) -> List[str]:
    mapping = {
        "order_id": "Your order number (e.g., A100).",
        "explanation": "A brief explanation of what happened.",
        "photo": "A photo/screenshot showing the issue or charge.",
        "return_initiated": "Confirmation that the return has been initiated (RMA or drop-off receipt).",
    }
    return [mapping.get(x, x) for x in reqs]

def _format_amount(cents: int | None) -> str:
    if not cents or cents < 0:
        return ""
    dollars = cents // 100
    rem = cents % 100
    return f"${dollars}.{rem:02d}"

def draft_reply(state: CaseState) -> DraftReply:
    llm = get_llm()
    snippets_md = _format_snippets(state.get("retrieved", []))

    meta = state["ticket"].metadata if state.get("ticket") else {}
    amount_cents = meta.get("amount_cents")
    amount_str = _format_amount(amount_cents)
    order_id = meta.get("order_id", "")

    approvals = state.get("approvals", {})
    actions_flag = approvals.get("actions", None)  # True | False | None
    plan = state.get("actions")
    escalated = _has_escalation(plan)
    missing = state.get("missing_requirements", [])

    # If we’re missing required evidence, ask for it explicitly.
    if missing:
        need_lines = "\n".join(f"- {x}" for x in _humanize_requirements(missing))
        prompt = f"""You are a support copilot.

Required information is missing; ask for ONLY the listed items. Do not promise a refund yet.

Ticket context:
- Order ID (if provided): {order_id or "(not provided)"}
- Requested refund amount: {amount_str or "(unspecified)"}

Required items:
{need_lines}

Rules:
- Be empathetic and concise.
- Use snippet citations like [n] only for policy lines.
- Do not mention any other dollar amounts than the requested refund (if provided).
- Output ONLY the final reply in Markdown.

Customer message:
\"\"\"{state["ticket"].text}\"\"\"

Snippets:
{snippets_md}
"""
        msg = llm.invoke([SystemMessage(content="Follow the instructions precisely."),
                          HumanMessage(content=prompt)])
        return DraftReply(ticket_id=state["ticket"].id, markdown=msg.content, citations=[])

    # Otherwise decide tone based on approvals/escalation.
    if actions_flag is True:
        disposition = "APPROVED"
        guidance = "State clearly that the refund has been initiated using the exact requested amount shown below and include timeline."
    elif actions_flag is False:
        disposition = "DENIED"
        guidance = "Explain politely that we cannot process the refund without approval; offer next steps."
    elif escalated:
        disposition = "ESCALATED"
        guidance = "Explain that the request exceeds automated limits and has been escalated to support; set expectations."
    else:
        disposition = "PENDING"
        guidance = "Do NOT imply the refund has been processed; say you can proceed once approval is confirmed."

    prompt = f"""You are a support copilot.

Decision: {disposition}
Guidance: {guidance}

Ticket context (must use exactly):
- Order ID (if provided): {order_id or "(not provided)"}
- Requested refund amount: {amount_str or "(unspecified)"}

Rules:
- If you mention a dollar amount, it MUST be exactly the requested refund amount above (do NOT mention policy caps like $50 in the amount line).
- You may reference policy limits from snippets with [n], but never substitute them for the refund amount.
- Keep it concise, empathetic, and action-oriented.
- Cite policy statements with [n].
- Output ONLY the final reply in Markdown.

Customer message:
\"\"\"{state["ticket"].text}\"\"\"

Snippets:
{snippets_md}
"""
    msg = llm.invoke([
        SystemMessage(content="Follow the instructions precisely."),
        HumanMessage(content=prompt),
    ])

    citations: List[str] = []
    for c in state.get("retrieved", []):
        src = c.get("source") or c.get("url") or c.get("doc_id")
        if src:
            citations.append(src)

    return DraftReply(ticket_id=state["ticket"].id, markdown=msg.content, citations=citations)
