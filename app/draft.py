# app/draft.py
import os
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from .state import CaseState, DraftReply

def get_llm():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it before running.")
    return ChatOpenAI(model="gpt-4o-mini", api_key=key)

_prompt = ChatPromptTemplate.from_messages([
    ("system", "Use ONLY the snippets provided. Cite claims using [n] markers referencing snippet indices. If info is missing, ask for it briefly."),
    ("user", "Ticket:\n{ticket}\n\nSnippets:\n{snippets}\n\nWrite a clear, empathetic reply.")
])

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
    return "\n".join(lines)

def draft_reply(state: CaseState) -> DraftReply:
    llm = get_llm()
    snippets_md = _format_snippets(state.get("retrieved", []))
    chain = _prompt | llm | StrOutputParser()
    md = chain.invoke({"ticket": state["ticket"].text, "snippets": snippets_md})

    # Build the citations list from retrieved items
    citations = []
    for c in state.get("retrieved", []):
        src = c.get("source") or c.get("url") or c.get("doc_id")
        if src:
            citations.append(src)

    return DraftReply(
        ticket_id=state["ticket"].id,
        markdown=md,
        citations=citations,
    )
