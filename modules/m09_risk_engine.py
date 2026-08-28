"""Module 9 -- Build evidence and calculate risk.
Implements the weighted formula from PROJECT_DOCUMENTATION.md Part 5.
All weights/thresholds are configurable prototype defaults, not values taken
from the problem statement itself.
"""

WEIGHTS = {
    "amount_risk": 0.15,
    "frequency_risk": 0.10,
    "counterparty_risk": 0.20,
    "protocol_risk": 0.15,
    "market_risk": 0.05,
    "behaviour_deviation": 0.20,
    "manipulation_score": 0.20,
}


def calculate_risk_score(evidence: dict) -> dict:
    """evidence must contain all WEIGHTS keys, plus optional
    'hard_violation' (bool) and 'blacklisted' (bool)."""

    weighted_sum = sum(evidence.get(key, 0) * weight for key, weight in WEIGHTS.items())
    weighted_sum = round(min(weighted_sum, 100), 1)

    forced = evidence.get("hard_violation", False) or evidence.get("blacklisted", False)
    final_score = 100.0 if forced else weighted_sum

    reasons = []
    for key, weight in WEIGHTS.items():
        val = evidence.get(key, 0)
        if val >= 60:
            reasons.append(f"{key} elevated ({val})")
    if evidence.get("hard_violation"):
        reasons.append("hard policy violation (limit/permission breach)")
    if evidence.get("blacklisted"):
        reasons.append("counterparty is blacklisted")
    if not reasons:
        reasons.append("all evidence within normal range")

    return {
        "risk_score": final_score,
        "weighted_raw_score": weighted_sum,
        "forced_override": forced,
        "evidence": evidence,
        "reasons": reasons,
    }
