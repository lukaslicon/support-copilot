# app/policy.py
from __future__ import annotations
from typing import List, Dict, Any

def required_evidence_for(
    *, cents: int, metadata: Dict[str, Any], text: str
) -> List[str]:
    """
    Return the list of evidence requirements the customer must satisfy
    BEFORE we approve/auto-run a refund at this amount.
    Names are simple keys used in drafts: 'order_id', 'explanation',
    'photo', 'return_initiated'.
    """
    needs: List[str] = []

    # Always need an order reference for any refund
    needs.append("order_id")

    # Explanation helps disambiguate; require for >= $10
    if cents >= 1000:
        needs.append("explanation")

    # For physical items or if a return is needed, require return initiated
    if metadata.get("physical_item") or metadata.get("requires_return"):
        needs.append("return_initiated")

    # For medium+ amounts (default >$20), require photo/evidence if flagged
    evidence_flag = metadata.get("evidence_required", False)
    if cents >= metadata.get("photo_threshold_cents", 2000) and (evidence_flag or metadata.get("physical_item")):
        needs.append("photo")

    # De-duplicate while preserving order
    seen = set()
    uniq = []
    for k in needs:
        if k not in seen:
            seen.add(k)
            uniq.append(k)
    return uniq


def which_missing(
    *, required: List[str], metadata: Dict[str, Any], text: str
) -> List[str]:
    """Given required keys, return which are missing from the ticket."""
    missing: List[str] = []
    has = {
        "order_id": bool(metadata.get("order_id")),
        "explanation": bool(metadata.get("explanation") or (text and len(text.strip()) >= 10)),
        "photo": bool(metadata.get("images")) and len(metadata.get("images") or []) > 0,
        "return_initiated": metadata.get("return_status") in {"initiated", "received"},
    }
    for k in required:
        if not has.get(k, False):
            missing.append(k)
    return missing
