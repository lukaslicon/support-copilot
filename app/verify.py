# Copyright Lukas Licon 2025. All Rights Reserved.

import re
from .state import CaseState

def verify_grounding(state: CaseState):
    md = state["draft"].markdown if state["draft"] else ""
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', md) if s.strip()]
    missing = [s for s in sentences if "[" not in s or "]" not in s]
    flags = []
    if missing:
        flags.append("UNGROUNDED_CLAIM")
    return {"policy_flags": flags}