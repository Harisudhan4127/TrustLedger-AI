"""Module 8 -- Compare with historical agent behaviour."""

from ml.behaviour_model import compute_behaviour_deviation


def compare_behaviour(conn, agent_id: str, amount: float) -> dict:
    profile = conn.execute(
        "SELECT * FROM behaviour_profiles WHERE agent_id = ?", (agent_id,)
    ).fetchone()

    if profile is None:
        # Brand-new agent with no baseline yet -- treat conservatively
        return {"behaviour_deviation": 40, "method": "no_baseline_yet"}

    history_rows = conn.execute(
        "SELECT amount FROM transactions WHERE agent_id = ? ORDER BY created_at DESC LIMIT 30",
        (agent_id,),
    ).fetchall()
    history_amounts = [r["amount"] for r in history_rows]

    result = compute_behaviour_deviation(
        mean_amount=profile["mean_amount"],
        std_amount=profile["std_amount"],
        current_amount=amount,
        history_amounts=history_amounts,
    )
    return result
