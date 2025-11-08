# Copyright Lukas Licon 2025. All Rights Reserved.

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from .state import CaseState
from .retriever import build_hybrid_retriever
from .classify import classify
from .draft import draft_reply
from .verify import verify_grounding
from .plan import plan_actions
from .hil import interrupt_approval
from .export import execute_plan

workflow = StateGraph(CaseState)

def ingest_ticket(state: CaseState):
    return {"ticket": state["ticket"]}

def classify_intent(state: CaseState):
    out = classify(state["ticket"].text)
    return {"intents": out.intents, "severity": out.severity}

_FAKE_CHUNKS = [
    {"text": "Refunds up to $50 within 30 days.", "meta": {"doc_id": "kb1", "url": "kb://refunds"}},
    {"text": "Refunds typically settle within 3–5 business days.", "meta": {"doc_id": "kb2", "url": "kb://settlement"}}
]
_retriever = build_hybrid_retriever(_FAKE_CHUNKS)

def retrieve_context(state: CaseState):
    hits = _retriever.invoke(state["ticket"].text)
    chunks = [{
        "doc_id": h.metadata.get("doc_id", ""),
        "source": h.metadata.get("url", ""),
        "text": h.page_content,
        "score": h.metadata.get("score", 0.0),
    } for h in hits]
    return {"retrieved": chunks}

def draft_node(state: CaseState):
    return {"draft": draft_reply(state)}

def verify_node(state: CaseState):
    return verify_grounding(state)

def plan_node(state: CaseState):
    plan, missing = plan_actions(state)
    out = {"actions": plan}
    if missing:
        out["missing_requirements"] = missing
    return out

def approval_node(state: CaseState):
    return interrupt_approval(state)

def execute_node(state: CaseState):
    plan = state.get("actions")
    if not plan:
        return {}

    has_escalation = any(s.tool == "notify" for s in plan.steps)
    approved = state.get("approvals", {}).get("actions") is True

    if not approved and not has_escalation:
        return {}  # needs approval for refund, and there is no escalation to run

    results = execute_plan(plan)
    return {"executed": results}

def export_node(state: CaseState):
    # export only if something executed
    if not state.get("executed"):
        return {}
    return {"artifacts": {"report_json": "file://tmp/report.json"}}

# nodes
workflow.add_node("ingest_ticket", ingest_ticket)
workflow.add_node("classify_intent", classify_intent)
workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("verify", verify_node)
workflow.add_node("plan", plan_node)
workflow.add_node("approval", approval_node)
workflow.add_node("draft", draft_node)      # <-- draft AFTER approval
workflow.add_node("execute", execute_node)
workflow.add_node("export", export_node)
workflow.add_node("close", lambda s: {})

# edges
workflow.add_edge(START, "ingest_ticket")
workflow.add_edge("ingest_ticket", "classify_intent")
workflow.add_edge("classify_intent", "retrieve_context")
workflow.add_edge("retrieve_context", "verify")
workflow.add_edge("verify", "plan")
workflow.add_edge("plan", "approval")
workflow.add_edge("approval", "draft")      # <-- draft after decision
workflow.add_edge("draft", "execute")
workflow.add_edge("execute", "export")
workflow.add_edge("export", "close")
workflow.add_edge("close", END)

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)