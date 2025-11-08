# Copyright Lukas Licon 2025. All Rights Reserved.

from typing import Optional, Literal, List, Dict, Tuple, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel
from operator import add
from datetime import datetime

class Ticket(BaseModel):
    id: str
    channel: Literal["email","chat","slack","form"]
    created_at: datetime
    customer_id: Optional[str] = None
    text: str
    metadata: Dict = {}

class RetrievalChunk(BaseModel):
    doc_id: str
    source: str
    text: str
    score: float
    span: Optional[Tuple[int,int]] = None

class DraftReply(BaseModel):
    ticket_id: str
    markdown: str
    citations: List[str]
    risk_flags: List[str] = []

class ActionStep(BaseModel):
    tool: Literal["refund","toggle_feature","file_bug","notify"]
    args: Dict
    guard: str
    rationale: str

class ActionPlan(BaseModel):
    ticket_id: str
    steps: List[ActionStep]
    requires_approval: bool = True

class ToolResult(BaseModel):
    tool: str
    ok: bool
    result: Dict = {}
    error: Optional[str] = None
    idempotency_key: Optional[str] = None

class CaseState(TypedDict):
    ticket: Ticket
    intents: Annotated[List[str], add]
    severity: Literal["low","normal","high"]
    retrieved: Annotated[List[RetrievalChunk], add]
    draft: Optional[DraftReply]
    actions: Optional[ActionPlan]
    approvals: Dict[str, bool]           # {"actions": True/False}
    executed: Annotated[List[ToolResult], add]
    artifacts: Dict[str, str]
    policy_flags: Annotated[List[str], add]