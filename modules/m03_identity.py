"""Module 3 -- Verify agent identity and active role.
Confirms the requesting agent's credentials and looks up its currently
assigned role and permission scope. This is a deterministic security check --
no AI/ML involved.
"""

from security.auth import verify_bearer_token


def verify_identity(conn, agent_id: str, raw_token: str) -> dict:
    """Returns {valid: bool, role_id, status, reason}"""
    row = conn.execute(
        "SELECT agent_id, role_id, api_token_hash, status FROM agents WHERE agent_id = ?",
        (agent_id,),
    ).fetchone()

    if row is None:
        return {"valid": False, "role_id": None, "reason": "unknown_agent"}

    if row["status"] != "active":
        return {"valid": False, "role_id": row["role_id"], "reason": "agent_suspended"}

    if not verify_bearer_token(raw_token, row["api_token_hash"]):
        return {"valid": False, "role_id": row["role_id"], "reason": "invalid_credential"}

    return {"valid": True, "role_id": row["role_id"], "reason": "ok"}
