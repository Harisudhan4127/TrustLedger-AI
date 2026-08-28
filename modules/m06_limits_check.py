"""Module 6 -- Evaluate amount, frequency, exposure and permissions.
Deterministic comparisons against the loaded policy set (Module 5) and the
agent's rolling financial state (spent-today, transactions-today).
"""

from datetime import datetime


def check_limits(conn, agent_id: str, action_type: str, amount: float,
                  role_id: str, policy: dict, allowed_action_types: list) -> dict:
    state_row = conn.execute(
        "SELECT * FROM financial_state WHERE agent_id = ?", (agent_id,)
    ).fetchone()

    daily_spent = state_row["daily_spent"] if state_row else 0.0
    txn_count_today = state_row["txn_count_today"] if state_row else 0

    permission_valid = action_type in allowed_action_types
    amount_within_limit = amount <= policy["max_single_txn"]
    daily_within_limit = (daily_spent + amount) <= policy["daily_limit"]
    frequency_exceeded = (txn_count_today + 1) > policy["max_frequency_per_day"]

    hard_violation = (not permission_valid) or (not amount_within_limit) or (not daily_within_limit)

    # Sub-scores 0-100, scaled proportionally against the limit (not just pass/fail)
    amount_risk = min(100, round((amount / policy["max_single_txn"]) * 60)) if policy["max_single_txn"] else 100
    frequency_risk = min(100, round(((txn_count_today + 1) / policy["max_frequency_per_day"]) * 70)) if policy["max_frequency_per_day"] else 100

    return {
        "permission_valid": permission_valid,
        "amount_within_limit": amount_within_limit,
        "daily_within_limit": daily_within_limit,
        "frequency_exceeded": frequency_exceeded,
        "hard_violation": hard_violation,
        "amount_risk": amount_risk,
        "frequency_risk": frequency_risk,
        "daily_spent_before": daily_spent,
        "txn_count_today_before": txn_count_today,
    }
