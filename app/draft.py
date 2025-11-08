# Copyright Lukas Licon 2025. All Rights Reserved.

import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import CaseState, DraftReply

def get_llm():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it before running.")
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

    approvals = state.get("approvals", {})
    actions_flag = approvals.get("actions", None)  # True | False | None (missing)

    if actions_flag is True:
        disposition = "APPROVED"
        guidance = "State clearly that the refund has been initiated and include the amount."
    elif actions_flag is False:
        disposition = "DENIED"
        guidance = "Explain politely that the refund cannot be processed without approval and outline next steps or alternatives."
    else:
        disposition = "PENDING"
        guidance = "Do NOT imply the refund has been processed. Offer to proceed as soon as approval is confirmed."

    prompt = f"""You are a support copilot.

Decision: {disposition}
Guidance: {guidance}

Rules:
- Ground policy statements in the snippets and cite with [n].
- Keep it concise, empathetic, and action-oriented.
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

    return DraftReply(
        ticket_id=state["ticket"].id,
        markdown=msg.content,
        citations=citations,
    )
