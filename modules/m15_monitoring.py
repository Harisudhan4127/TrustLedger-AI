"""Module 15 -- Monitor drift, incidents and policy/model performance.
Zooms out from a single transaction to system-level health: decision
distribution, escalation rate, and per-agent incident counts (which are a
proxy for possible drift / repeated manipulation attempts).
"""

from datetime import datetime


def log_incident(conn, txn_id, agent_id, incident_type, details):
    conn.execute(
        """INSERT INTO incidents (txn_id, agent_id, incident_type, details, created_at)
           VALUES (?,?,?,?,?)""",
        (txn_id, agent_id, incident_type, details, datetime.utcnow().isoformat()),
    )
    conn.commit()


def decision_distribution(conn) -> dict:
    rows = conn.execute(
        "SELECT decision, COUNT(*) as c FROM decisions GROUP BY decision"
    ).fetchall()
    return {r["decision"]: r["c"] for r in rows}


def agent_incident_counts(conn) -> list:
    rows = conn.execute(
        """SELECT agent_id, COUNT(*) as incident_count
           FROM incidents GROUP BY agent_id ORDER BY incident_count DESC"""
    ).fetchall()
    return [dict(r) for r in rows]


def escalation_rate(conn) -> float:
    total = conn.execute("SELECT COUNT(*) as c FROM decisions").fetchone()["c"]
    if total == 0:
        return 0.0
    escalated = conn.execute(
        "SELECT COUNT(*) as c FROM decisions WHERE decision = 'ESCALATE'"
    ).fetchone()["c"]
    return round((escalated / total) * 100, 1)
