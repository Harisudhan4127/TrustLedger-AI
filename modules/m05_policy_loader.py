"""Module 5 -- Load applicable role and transaction policies."""

import json


def load_policy(conn, role_id: str) -> dict:
    row = conn.execute(
        "SELECT * FROM policies WHERE role_id = ? ORDER BY policy_id DESC LIMIT 1",
        (role_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "max_single_txn": row["max_single_txn"],
        "daily_limit": row["daily_limit"],
        "max_frequency_per_day": row["max_frequency_per_day"],
        "allowed_counterparties": json.loads(row["allowed_counterparties"] or "[]"),
        "allowed_protocols": json.loads(row["allowed_protocols"] or "[]"),
    }
