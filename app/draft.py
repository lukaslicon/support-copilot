# Copyright Lukas Licon 2025. All Rights Reserved.

import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage  # <-- needed
from .state import CaseState, DraftReply

def get_llm():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it before running.")
    # Low-latency model; set temperature=0 for consistent outputs
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=key)

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

def draft_reply(state: CaseState) -> DraftReply:
    llm = get_llm()
    snippets_md = _format_snippets(state.get("retrieved", []))

    approved = bool(state.get("approvals", {}).get("actions"))
    status_line = (
        "Approval status: APPROVED. If actions were executed, reflect that in your wording."
        if approved else
        "Approval status: PENDING. DO NOT state that a refund was processed. Use conditional language like 'I can submit the refund as soon as I have your confirmation.'"
    )

    prompt = f"""You are a support copilot. {status_line}

Rules:
- Use ONLY the provided snippets; cite claims with [n].
- If PENDING, avoid language implying the refund has already been processed.
- If APPROVED, you may state that the refund has been initiated.
- Be concise, empathetic, and action-oriented.
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

    # Build citations from retrieved items
    citations: List[str] = []
    for c in state.get("retrieved", []):
        src = c.get("source") or c.get("url") or c.get("doc_id")
        if src:
            citations.append(src)

    return DraftReply(
        ticket_id=state["ticket"].id,
        markdown=msg.content,
        citations=citations,
    )
