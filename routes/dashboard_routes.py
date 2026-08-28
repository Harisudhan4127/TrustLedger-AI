"""API endpoints feeding the live dashboard (Part 15 of the documentation)."""

import json

from flask import Blueprint, jsonify, render_template

from database.db import get_db
from modules import m13_ledger, m15_monitoring

dashboard_bp = Blueprint("dashboard_bp", __name__)


@dashboard_bp.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@dashboard_bp.route("/api/overview")
def api_overview():
    conn = get_db()
    dist = m15_monitoring.decision_distribution(conn)
    esc_rate = m15_monitoring.escalation_rate(conn)
    incidents = m15_monitoring.agent_incident_counts(conn)
    chain_ok = m13_ledger.verify_chain(conn)
    conn.close()
    return jsonify({
        "decision_distribution": dist,
        "escalation_rate": esc_rate,
        "agent_incidents": incidents,
        "ledger_integrity_ok": chain_ok,
    })


@dashboard_bp.route("/api/agents")
def api_agents():
    conn = get_db()
    rows = conn.execute(
        """SELECT a.agent_id, a.name, a.role_id, a.status, b.mean_amount, b.std_amount,
                  b.sample_count, f.daily_spent, f.txn_count_today
           FROM agents a
           LEFT JOIN behaviour_profiles b ON a.agent_id = b.agent_id
           LEFT JOIN financial_state f ON a.agent_id = f.agent_id"""
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@dashboard_bp.route("/api/transactions")
def api_transactions():
    conn = get_db()
    rows = conn.execute(
        """SELECT t.txn_id, t.agent_id, t.action_type, t.amount, t.currency,
                  t.counterparty_id, t.created_at, d.decision, d.reason,
                  d.review_status, r.risk_score
           FROM transactions t
           LEFT JOIN decisions d ON t.txn_id = d.txn_id
           LEFT JOIN risk_assessments r ON t.txn_id = r.txn_id
           ORDER BY t.created_at DESC LIMIT 50"""
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@dashboard_bp.route("/api/transaction/<txn_id>")
def api_transaction_detail(txn_id):
    conn = get_db()
    txn = conn.execute("SELECT * FROM transactions WHERE txn_id=?", (txn_id,)).fetchone()
    risk = conn.execute("SELECT * FROM risk_assessments WHERE txn_id=?", (txn_id,)).fetchone()
    decision = conn.execute("SELECT * FROM decisions WHERE txn_id=?", (txn_id,)).fetchone()
    conn.close()
    if not txn:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "transaction": dict(txn),
        "risk_assessment": dict(risk) if risk else None,
        "decision": dict(decision) if decision else None,
    })


@dashboard_bp.route("/api/review-queue")
def api_review_queue():
    conn = get_db()
    rows = conn.execute(
        """SELECT t.txn_id, t.agent_id, t.action_type, t.amount, t.counterparty_id,
                  r.risk_score, d.reason
           FROM decisions d
           JOIN transactions t ON t.txn_id = d.txn_id
           LEFT JOIN risk_assessments r ON r.txn_id = t.txn_id
           WHERE d.decision = 'ESCALATE' AND d.review_status = 'pending'
           ORDER BY t.created_at DESC"""
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@dashboard_bp.route("/api/blocked")
def api_blocked():
    conn = get_db()
    rows = conn.execute(
        """SELECT t.txn_id, t.agent_id, t.action_type, t.amount, t.counterparty_id,
                  r.risk_score, d.reason, t.created_at
           FROM decisions d
           JOIN transactions t ON t.txn_id = d.txn_id
           LEFT JOIN risk_assessments r ON r.txn_id = t.txn_id
           WHERE d.decision = 'BLOCK'
           ORDER BY t.created_at DESC LIMIT 50"""
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@dashboard_bp.route("/api/ledger")
def api_ledger():
    conn = get_db()
    rows = conn.execute("SELECT * FROM audit_log ORDER BY log_id DESC LIMIT 50").fetchall()
    conn.close()
    out = []
    for r in rows:
        d = dict(r)
        d["entry_json"] = json.loads(d["entry_json"])
        out.append(d)
    return jsonify(out)
