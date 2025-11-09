# Support Copilot (LangGraph)

A human-in-the-loop support copilot that triages **refund requests** using **policy + evidence**, routes by **amount tiers** (low / medium / high), and executes actions (refund or escalation) with a clear approval gate. Built with **LangGraph + LangChain**, open source and company-agnostic.

---

## Features

### Evidence-aware policy
- Requires specific items before acting (e.g., `order_id`, short explanation, photo/screenshot, return status for physical items).
- If anything’s missing → drafts a friendly “please provide …” reply (no approval, no execution).
- Global policy blocks (e.g., `chargeback_open`, `nonrefundable`, `outside_window`) auto-escalate to support.

### Tiered automation
- **Low** (≤ `LOW_THRESHOLD_CENTS`) → **auto-refund** (no HIL).
- **Medium** (`LOW` < amount ≤ `MEDIUM`) → **Human-in-the-Loop** (Approve / Deny / Defer).
- **High** (> `MEDIUM` or > `REFUND_CAP_CENTS`) → auto-**escalate** (via `notify` tool).

### Decision-aware drafting
- Uses the **exact requested amount** (never substitutes policy caps).
- Tones reflect outcome: **Approved**, **Denied**, **Pending**, **Escalated**, or **Missing evidence**.
- Can cite policy snippets with `[n]`.

### Tools
- `refund` (mock) → returns `{ refund_id, amount }`.
- `notify` (mock) → queues an escalation (e.g., email to support).

### Dev utilities
- `run.py` simulates a ticket; pass evidence and choose HIL decisions.
- `test_harness.py` runs one scenario per category with a compact summary.

---

## Roadmap

### Phase 1 – Durability & Correctness
- [ ] SQLite checkpointer for conversation persistence
- [ ] Persist FAISS index/docstore to disk
- [ ] Idempotency keys for tools (prevent double refunds)
- [ ] Token/latency/cost logging and retry/backoff

### Phase 2 – Channel Adapters
- [ ] Email ingest:
  - Extract `order_id` from subject/body
  - Parse attachments → `images`
  - Body → `explanation`
- [ ] Chat/webhook adapters (Slack/Discord/Intercom)
- [ ] Web form endpoint (structured inputs → metadata)

### Phase 3 – API & Reviewer UI
- [ ] FastAPI service:
  - `POST /tickets`
  - `POST /approve` / `POST /deny` / `POST /defer`
  - `GET /runs/:id`
- [ ] Minimal reviewer UI:
  - View plan, context, draft
  - Approve/Deny/Defer buttons
  - Upload missing evidence

### Phase 4 – Company Integration
- [ ] Pluggable policy packs (YAML/JSON → `policy.py`)
- [ ] Secrets management and `.env.example`
- [ ] Dockerfile and `docker-compose.yml` for deployment

### Phase 5 – Quality & Safety
- [ ] E2E evals with labeled tickets (tiering, evidence gate, tone)
- [ ] PII scrubbing and allowlist for order IDs
- [ ] Structured audit logs per run
