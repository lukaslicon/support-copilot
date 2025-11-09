Support Copilot (LangGraph)

A human-in-the-loop support copilot that triages refund requests using policy + evidence, routes by amount tiers (low/medium/high), and executes actions (refund or escalation) with a clear approval gate. Built with LangGraph + LangChain, open source and company-agnostic.

Features
Evidence-aware policy

Requires specific items before acting (e.g., order_id, short explanation, photo/screenshot, return status for physical items).

If anything’s missing → drafts a friendly “please provide …” reply (no approval, no execution).

Global policy blocks (e.g., chargeback_open, nonrefundable, outside_window) auto-escalate to support.

Tiered automation

Low (≤ LOW_THRESHOLD_CENTS) → auto-refund (no HIL).

Medium (LOW < amount ≤ MEDIUM) → Human-in-the-Loop (Approve / Deny / Defer).

High (> MEDIUM or > REFUND_CAP_CENTS) → auto-escalate (via notify tool).

Decision-aware drafting

Uses the exact requested amount (never substitutes policy caps).

Tones reflect outcome: Approved, Denied, Pending, Escalated, or Missing evidence.

Can cite policy snippets with [n].

Tools

refund (mock) → returns { refund_id, amount }.

notify (mock) → queues an escalation (e.g., email to support).

Dev utilities

run.py simulates a ticket, lets you pass evidence + choose HIL decisions.

test_harness.py runs one scenario per category with a compact summary.

Quickstart
python -m venv .venv
# Windows PowerShell:
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt


Set environment variables (examples):

$env:OPENAI_API_KEY = "<your-key>"
$env:LOW_THRESHOLD_CENTS = "2000"
$env:MEDIUM_THRESHOLD_CENTS = "5000"
$env:REFUND_CAP_CENTS = "5000"
$env:SUPPORT_ESCALATION_EMAIL = "support@example.com"


Run a few examples:

# Low (auto-refund)
python .\run.py --amount-cents 1500 --order-id A100 --text "double charged" --explanation "charged twice"

# Medium (HIL) with full evidence → prompt Approve / Deny / Defer
python .\run.py --amount-cents 2800 --order-id A100 --text "refund" --physical-item --return-status initiated --image proof.png --explanation "charged twice"

# Missing evidence (asks customer)
python .\run.py --amount-cents 2800 --no-order-id --text "refund"

# High (escalate)
python .\run.py --amount-cents 6000 --order-id A100 --text "refund" --explanation "charged twice"

# Batch tests
python .\test_harness.py

Roadmap

Phase 1 – Durability & correctness

SQLite checkpointer for conversation persistence.

Persist FAISS index/docstore to disk.

Idempotency keys for tools (avoid double refunds).

Token/latency/cost logging & retry/backoff.

Phase 2 – Channel adapters

Email ingest (extract order_id, parse attachments → images, body → explanation).

Chat/webhook adapters (Slack/Discord/Intercom).

Web form endpoint (structured inputs → metadata).

Phase 3 – API & reviewer UI

FastAPI service: POST /tickets, POST /approve|deny|defer, GET /runs/:id.

Minimal reviewer UI to view plan, context, draft, and Approve/Deny/Defer.

Phase 4 – Company integration

Pluggable policy packs (YAML/JSON → policy.py).

Secrets management + .env.example.

Dockerfile / docker-compose for easy deployment.

Phase 5 – Quality & safety

E2E evals with labeled cases (tiering, evidence gate, tone).

PII scrubbing & allowlist for order IDs.

Structured audit logs per run.
