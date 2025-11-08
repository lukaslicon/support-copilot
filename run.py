# run.py
from datetime import datetime
from langgraph.graph import Command
from app.graph import graph
from app.state import Ticket

cfg = {"configurable": {"thread_id": "case-0001"}}

initial = {
  "ticket": Ticket(id="t_1", channel="email", created_at=datetime.utcnow(),
                   customer_id="cust_9", text="I was double charged last week."),
  "intents": [], "retrieved": [], "policy_flags": [], "approvals": {},
  "draft": None, "actions": None, "executed": [], "artifacts": {}, "severity": "normal"
}

print(">> Running until approval...")
events = list(graph.stream(initial, cfg))

# the last event will contain an interrupt asking for approval
interrupt_payload = events[-1].get("__interrupt__")
if interrupt_payload:
    print("Approval requested. Proposed plan:\n", interrupt_payload["value"]["plan"])
    # simulate a human clicking "approve"
    decision = {"approved": True}
    print("\n>> Resuming with approval...")
    for e in graph.stream(Command(resume=decision), cfg):
        pass

final_state = graph.get_state(cfg).values
print("\n--- DRAFT REPLY ---")
print(final_state["draft"].markdown)
print("\n--- EXECUTION RESULTS ---")
print(final_state["executed"])
print("\n--- ARTIFACTS ---")
print(final_state["artifacts"])