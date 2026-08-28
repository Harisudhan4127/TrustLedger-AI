"""Routes exposing Module 1 (Action Intent API) over HTTP."""

from flask import Blueprint, request, jsonify

from modules.pipeline import run_pipeline

agent_bp = Blueprint("agent_bp", __name__)


@agent_bp.route("/agent/intent", methods=["POST"])
def submit_intent():
    payload = request.get_json(force=True, silent=True) or {}

    auth_header = request.headers.get("Authorization", "")
    raw_token = auth_header.replace("Bearer ", "").strip()

    if not payload.get("agent_id") or not raw_token:
        return jsonify({"error": "agent_id (in body) and Authorization bearer token are required"}), 400

    result = run_pipeline(payload, raw_token)
    status_code = 200 if result["decision"] != "BLOCK" or result["txn_id"] else 200
    return jsonify(result), status_code
