# Copyright Lukas Licon 2025. All Rights Reserved.
import re
from .state import CaseState

def verify_grounding(state: CaseState):
    md = state["draft"].markdown if state.get("draft") else ""
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', md) if s.strip()]
    # Only flag sentences that lack a numeric [n] citation
    missing = [s for s in sentences if not re.search(r"\[\d+\]", s)]
    flags = []
    if missing:
        flags.append("UNGROUNDED_CLAIM")
    return {"policy_flags": flags}
