"""Module 10 -- Decision Governor.
The single, deterministic authority that turns a risk score into a graduated
decision. Intentionally NOT a black box -- pure threshold + override logic,
fully auditable and unit-testable. AI-derived evidence has already been
folded into risk_score by Module 9; this function never calls an LLM.
"""

BANDS = [
    (0, 30, "EXECUTE"),
    (31, 60, "CONSTRAIN"),
    (61, 80, "ESCALATE"),
    (81, 100, "BLOCK"),
]


def govern(risk_result: dict, policy_amount_limit: float, requested_amount: float) -> dict:
    score = risk_result["risk_score"]

    decision = "BLOCK"
    for low, high, label in BANDS:
        if low <= score <= high:
            decision = label
            break

    reason = f"risk_score={score} -> {decision}. " + "; ".join(risk_result["reasons"])

    applied_amount = requested_amount
    if decision == "CONSTRAIN" and requested_amount > policy_amount_limit:
        applied_amount = policy_amount_limit
        reason += f" | Amount constrained from {requested_amount} to policy limit {policy_amount_limit}."

    return {
        "decision": decision,
        "reason": reason,
        "risk_score": score,
        "applied_amount": applied_amount,
    }
