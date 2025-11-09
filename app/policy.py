# Copyright Lukas Licon 2025. All Rights Reserved.

from __future__ import annotations
from typing import List, Dict, Any, Tuple
from .config import EXPLANATION_MIN_CHARS

def required_evidence_for(*, cents: int, metadata: Dict[str, Any], text: str) -> List[str]:
    needs: List[str] = []
    needs.append("order_id")

    # Default rule: explanation for >= $10
    explanation_required = cents >= 1000

    # If it's a physical item AND we already have a photo + return started,
    # relax the explanation requirement.
    if metadata.get("physical_item") and metadata.get("return_status") in {"initiated","received"}:
        has_photo = bool(metadata.get("images")) and len(metadata.get("images") or []) > 0
        if has_photo:
            explanation_required = False

    if explanation_required:
        needs.append("explanation")

    if metadata.get("physical_item") or metadata.get("requires_return"):
        needs.append("return_initiated")

    evidence_flag = metadata.get("evidence_required", False)
    if cents >= metadata.get("photo_threshold_cents", 2000) and (evidence_flag or metadata.get("physical_item")):
        needs.append("photo")

    # de-dupe
    seen, uniq = set(), []
    for k in needs:
        if k not in seen:
            seen.add(k); uniq.append(k)
    return uniq


def policy_blocks_auto(meta: Dict[str, Any]) -> Tuple[bool, str]:
    # timing
    if meta.get("outside_window"):
        return True, "outside_window"
    # product type
    if meta.get("nonrefundable") or meta.get("gift_card"):
        return True, "nonrefundable"
    if meta.get("digital_item_delivered") and not meta.get("evidence_of_non_delivery"):
        return True, "digital_delivered"
    # disputes / risk
    if meta.get("chargeback_open"):
        return True, "chargeback_open"
    if meta.get("fraud_score", 0) >= int(meta.get("fraud_threshold", 80)):
        return True, "high_risk"
    # payment method
    if meta.get("payment_method") in {"wire", "crypto"}:
        return True, "payment_method"
    # cumulative behavior
    if meta.get("recent_refund_count", 0) >= int(meta.get("refund_rate_limit", 3)):
        return True, "refund_rate_limited"
    # manual review
    if meta.get("manual_review_hold"):
        return True, "manual_hold"
    return False, ""

def which_missing(
    *, required: List[str], metadata: Dict[str, Any], text: str
) -> List[str]:
    """Given required keys, return which are missing from the ticket."""
    missing: List[str] = []
    has = {
        "order_id": bool(metadata.get("order_id")),
        "explanation": bool(metadata.get("explanation") or (text and len(text.strip()) >= EXPLANATION_MIN_CHARS)),
        "photo": bool(metadata.get("images")) and len(metadata.get("images") or []) > 0,
        "return_initiated": metadata.get("return_status") in {"initiated", "received"},
    }
    for k in required:
        if not has.get(k, False):
            missing.append(k)
    return missing
