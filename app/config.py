# Copyright Lukas Licon 2025. All Rights Reserved.

import os

def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

# Dollar thresholds expressed in cents
REFUND_CAP_CENTS              = _int("REFUND_CAP_CENTS", 5000)   # $50 policy cap
LOW_THRESHOLD_CENTS           = _int("LOW_THRESHOLD_CENTS", 2000) # <=$20 auto
MEDIUM_THRESHOLD_CENTS        = _int("MEDIUM_THRESHOLD_CENTS", 5000) # >$20 & <=$50 => HIL
# Anything > MEDIUM_THRESHOLD_CENTS is high → deny+escalate

EXPLANATION_MIN_CHARS = int(os.getenv("EXPLANATION_MIN_CHARS", "0"))

# Models
OPENAI_CHAT_MODEL             = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL            = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# Escalation
SUPPORT_ESCALATION_EMAIL      = os.getenv("SUPPORT_ESCALATION_EMAIL", "support@example.com")
