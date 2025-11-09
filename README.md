ChatGPT said:
Support Copilot (LangGraph) 🛟

A human-in-the-loop support copilot that triages refund requests using policy + evidence, routes by amount tiers (low/medium/high), and executes actions (refund or escalation) with a clear approval gate. Built with LangGraph + LangChain, designed to be open source and company-agnostic.

✨ What it does today

Evidence-aware policy

Requires specific items before acting (e.g., order_id, short explanation, photo/screenshot, return status for physical items).

If required evidence is missing → drafts a friendly “please provide …” message (no approval, no execution).

Global policy blocks (e.g., chargeback_open, nonrefundable, outside_window, etc.) automatically escalate to support.

Tiered automation by amount

Low (≤ LOW_THRESHOLD_CENTS) → auto-refund (no HIL).

Medium (LOW < amount ≤ MEDIUM) → Human-in-the-Loop (Approve / Deny / Defer).

High (> MEDIUM or > REFUND_CAP_CENTS) → auto-escalate (notify tool).

Decision-aware drafting

Uses the exact requested amount (never substitutes policy caps).

Tones:

Approved: “Refund of $X.XX initiated…”

Denied: “Cannot process without approval…”

Pending: “Awaiting approval…”

Escalated: “Exceeds automated limits; escalated…”

Missing evidence: bullet list of what to send next

Cites policy snippets as [n] when available.

Tools

refund (mock) → returns { refund_id, amount }.

notify (mock) → queues an escalation (e.g., email to support).

CLI + Test Harness

run.py simulates a ticket, lets you pass evidence and choose HIL decisions.

test_harness.py runs one scenario per category and prints a compact summary.

🧱 Repo layout (key files)
app/
  config.py   # thresholds, models, escalation email (env-overridable)
  graph.py    # LangGraph nodes & edges; approval → draft → execute
  plan.py     # policy + tiering → ActionPlan (or missing requirements)
  policy.py   # evidence rules + global policy blocks
  draft.py    # decision-aware reply drafting (uses exact amount)
  retriever.py# hybrid retriever (BM25 + embeddings)
  tools.py    # refund + notify (mock) tools
  export.py   # executes planned steps
  state.py    # Pydantic models: Ticket, ActionPlan, ActionStep, DraftReply, ToolResult
run.py        # CLI runner
test_harness.py # batch tests across categories

🚀 Quickstart
1) Install
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# If you use Pydantic EmailStr anywhere, also:
# pip install "pydantic[email]"

2) Configure (env vars)
# OpenAI
$env:OPENAI_API_KEY = "<your-key>"
$env:OPENAI_CHAT_MODEL = "gpt-4o-mini"
$env:OPENAI_EMBED_MODEL = "text-embedding-3-small"

# Policy thresholds (cents)
$env:LOW_THRESHOLD_CENTS = "2000"        # <= $20 → auto-refund
$env:MEDIUM_THRESHOLD_CENTS = "5000"     # >$20 & <=$50 → HIL
$env:REFUND_CAP_CENTS = "5000"           # >$50 → escalate

# Evidence strictness (optional)
$env:EXPLANATION_MIN_CHARS = "10"

# Escalation destination
$env:SUPPORT_ESCALATION_EMAIL = "support@example.com"

3) Run a single ticket
# Low (auto-refund)
python .\run.py --amount-cents 1500 --order-id A100 --text "double charged" --explanation "charged twice"

# Medium (HIL) with full evidence
python .\run.py --amount-cents 2800 --order-id A100 --text "refund" --physical-item --return-status initiated --image proof.png --explanation "charged twice"
# You'll be prompted: Approve / Deny / Defer

# Missing evidence (asks customer)
python .\run.py --amount-cents 2800 --no-order-id --text "refund"

# High (escalate)
python .\run.py --amount-cents 6000 --order-id A100 --text "refund" --explanation "charged twice"