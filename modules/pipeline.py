"""Orchestrates the full 15-module TrustLedger-AI security loop for a single incoming
agent intent. This is the function routes/agent_routes.py calls -- it exists
purely to wire the modules together in order, with no business logic of its
own.
"""

import json
from datetime import datetime

from database.db import get_db
from modules import (
    m01_intent, m02_normalize, m03_identity, m04_manipulation,
    m05_policy_loader, m06_limits_check, m07_context_risk, m08_behaviour,
    m09_risk_engine, m10_decision_governor, m11_transaction_service,
    m12_outcome, m13_ledger, m14_baseline_update, m15_monitoring,
)
from ml.manipulation_llm import semantic_manipulation_check
import uuid


def run_pipeline(payload: dict, raw_token: str) -> dict:
    conn = get_db()
    try:
        # 1. Intent
        intent_event = m01_intent.capture_intent(payload)

        # 2. Normalize
        action = m02_normalize.normalize(payload)
        agent_id = action["agent_id"]

        # 3. Identity
        identity = m03_identity.verify_identity(conn, agent_id, raw_token)
        if not identity["valid"]:
            return _reject_early(conn, intent_event, action, f"identity_check_failed:{identity['reason']}")

        role_id = identity["role_id"]
        role_row = conn.execute("SELECT allowed_action_types FROM roles WHERE role_id=?", (role_id,)).fetchone()
        allowed_action_types = json.loads(role_row["allowed_action_types"]) if role_row else []

        # 4. Manipulation detection
        rule_result = m04_manipulation.detect_manipulation(action["raw_instruction"])
        llm_result = semantic_manipulation_check(role_id, "role policy summary", action["raw_instruction"])
        manipulation_score = rule_result["manipulation_score"]
        manipulation_flags = rule_result["flags"]
        if llm_result:
            manipulation_score = max(manipulation_score, llm_result.get("manipulation_score", 0))
            manipulation_flags += llm_result.get("flags", [])

        # 5. Load policy
        policy = m05_policy_loader.load_policy(conn, role_id)
        if policy is None:
            return _reject_early(conn, intent_event, action, "no_policy_configured_for_role")

        # 6. Limits check
        limits = m06_limits_check.check_limits(
            conn, agent_id, action["action_type"], action["amount"],
            role_id, policy, allowed_action_types,
        )

        # 7. Context risk
        context = m07_context_risk.evaluate_context(conn, action["destination"])

        # 8. Behaviour
        behaviour = m08_behaviour.compare_behaviour(conn, agent_id, action["amount"])

        # 9. Risk engine
        evidence = {
            "amount_risk": limits["amount_risk"],
            "frequency_risk": limits["frequency_risk"],
            "counterparty_risk": context["counterparty_risk"],
            "protocol_risk": context["protocol_risk"],
            "market_risk": context["market_risk"],
            "behaviour_deviation": behaviour["behaviour_deviation"],
            "manipulation_score": manipulation_score,
            "hard_violation": limits["hard_violation"],
            "blacklisted": context["blacklisted"],
        }
        risk_result = m09_risk_engine.calculate_risk_score(evidence)

        # 10. Decision Governor
        governed = m10_decision_governor.govern(risk_result, policy["max_single_txn"], action["amount"])
        decision = governed["decision"]

        # Persist the transaction record regardless of outcome
        txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow().isoformat()
        conn.execute(
            """INSERT INTO transactions
               (txn_id, agent_id, action_type, amount, currency, counterparty_id,
                protocol, raw_instruction, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (txn_id, agent_id, action["action_type"], action["amount"], action["currency"],
             action["destination"], action["protocol"], action["raw_instruction"], now),
        )
        conn.execute(
            """INSERT INTO risk_assessments
               (txn_id, amount_risk, frequency_risk, counterparty_risk, protocol_risk,
                market_risk, behaviour_deviation, manipulation_score, risk_score, evidence_json)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (txn_id, limits["amount_risk"], limits["frequency_risk"], context["counterparty_risk"],
             context["protocol_risk"], context["market_risk"], behaviour["behaviour_deviation"],
             manipulation_score, risk_result["risk_score"], json.dumps(risk_result, default=str)),
        )
        review_status = "pending" if decision == "ESCALATE" else None
        conn.execute(
            """INSERT INTO decisions (txn_id, decision, reason, review_status, decided_at)
               VALUES (?,?,?,?,?)""",
            (txn_id, decision, governed["reason"], review_status, now),
        )
        conn.commit()

        execution_result = None
        # 11 & 12. Execute + capture outcome (only for EXECUTE / CONSTRAIN)
        if decision in ("EXECUTE", "CONSTRAIN"):
            execution_result = m11_transaction_service.execute_transaction(
                agent_id, governed["applied_amount"], action["destination"], action["currency"],
            )
            m12_outcome.capture_outcome(conn, agent_id, governed["applied_amount"])

        # Incidents
        if limits["hard_violation"]:
            m15_monitoring.log_incident(conn, txn_id, agent_id, "policy_violation", governed["reason"])
        if manipulation_score >= 60:
            m15_monitoring.log_incident(conn, txn_id, agent_id, "manipulation_detected",
                                         f"flags={manipulation_flags}")

        # 13. Ledger (always written, including BLOCK/ESCALATE)
        ledger_entry = {
            "txn_id": txn_id, "agent_id": agent_id, "decision": decision,
            "risk_score": risk_result["risk_score"], "evidence": evidence,
            "reason": governed["reason"], "manipulation_flags": manipulation_flags,
            "execution_result": execution_result,
        }
        entry_hash = m13_ledger.write_ledger_entry(conn, txn_id, ledger_entry)

        # 14. Baseline update (only for completed, non-blocked transactions)
        if decision in ("EXECUTE", "CONSTRAIN"):
            m14_baseline_update.update_baseline(conn, agent_id)

        return {
            "txn_id": txn_id,
            "decision": decision,
            "risk_score": risk_result["risk_score"],
            "reason": governed["reason"],
            "evidence": evidence,
            "manipulation_flags": manipulation_flags,
            "execution_result": execution_result,
            "ledger_hash": entry_hash,
        }
    finally:
        conn.close()


def _reject_early(conn, intent_event, action, reason):
    conn.close()
    return {
        "txn_id": None,
        "decision": "BLOCK",
        "risk_score": 100,
        "reason": reason,
        "evidence": {},
        "manipulation_flags": [],
        "execution_result": None,
        "ledger_hash": None,
    }
