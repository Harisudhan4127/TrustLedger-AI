"""Human Escalation review actions (Approve / Modify / Reject) -- the human
step inside the dashed box in the architecture diagram."""

from datetime import datetime

from flask import Blueprint, jsonify, request

from database.db import get_db
from modules import m11_transaction_service, m12_outcome, m13_ledger, m14_baseline_update

review_bp = Blueprint("review_bp", __name__)


@review_bp.route("/api/review/<txn_id>", methods=["POST"])
def review_transaction(txn_id):
    body = request.get_json(force=True, silent=True) or {}
    action = body.get("action")  # "approve" | "modify" | "reject"
    reviewer = body.get("reviewed_by", "human_reviewer")
    modified_amount = body.get("modified_amount")

    if action not in ("approve", "modify", "reject"):
        return jsonify({"error": "action must be approve, modify, or reject"}), 400

    conn = get_db()
    txn = conn.execute("SELECT * FROM transactions WHERE txn_id=?", (txn_id,)).fetchone()
    decision_row = conn.execute("SELECT * FROM decisions WHERE txn_id=?", (txn_id,)).fetchone()

    if not txn or not decision_row or decision_row["decision"] != "ESCALATE":
        conn.close()
        return jsonify({"error": "transaction not found or not pending escalation"}), 404

    now = datetime.utcnow().isoformat()
    execution_result = None

    if action == "reject":
        new_status = "rejected"
    else:
        new_status = "approved" if action == "approve" else "modified"
        amount = modified_amount if (action == "modify" and modified_amount) else txn["amount"]
        execution_result = m11_transaction_service.execute_transaction(
            txn["agent_id"], amount, txn["counterparty_id"], txn["currency"],
        )
        m12_outcome.capture_outcome(conn, txn["agent_id"], amount)
        m14_baseline_update.update_baseline(conn, txn["agent_id"])

    conn.execute(
        "UPDATE decisions SET review_status=?, reviewed_by=? WHERE txn_id=?",
        (new_status, reviewer, txn_id),
    )
    conn.commit()

    m13_ledger.write_ledger_entry(conn, txn_id, {
        "txn_id": txn_id, "human_review": new_status, "reviewer": reviewer,
        "execution_result": execution_result, "timestamp": now,
    })
    conn.close()

    return jsonify({"txn_id": txn_id, "review_status": new_status, "execution_result": execution_result})
