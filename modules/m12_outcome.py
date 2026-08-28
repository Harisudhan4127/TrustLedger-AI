"""Module 12 -- Capture outcome and financial state.
Updates the agent's rolling daily-spend / transaction-count state after a
transaction actually executes (EXECUTE or CONSTRAIN outcomes only).
"""

from datetime import datetime


def capture_outcome(conn, agent_id: str, amount_executed: float):
    row = conn.execute("SELECT * FROM financial_state WHERE agent_id = ?", (agent_id,)).fetchone()
    now = datetime.utcnow().isoformat()

    if row is None:
        conn.execute(
            "INSERT INTO financial_state (agent_id, daily_spent, txn_count_today, window_start) VALUES (?,?,?,?)",
            (agent_id, amount_executed, 1, now),
        )
    else:
        conn.execute(
            "UPDATE financial_state SET daily_spent = daily_spent + ?, txn_count_today = txn_count_today + 1 WHERE agent_id = ?",
            (amount_executed, agent_id),
        )
    conn.commit()
