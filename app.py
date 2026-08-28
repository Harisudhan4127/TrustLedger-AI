"""TrustLedger-AI -- Risk-Aware Autonomy Layer for Financial AI Agents.
Flask app entrypoint. Run with: python app.py
"""

import os

from flask import Flask, jsonify, redirect

from database.db import init_db, DB_PATH
from routes.agent_routes import agent_bp
from routes.dashboard_routes import dashboard_bp
from routes.review_routes import review_bp
from utils.scenarios import SCENARIOS

app = Flask(__name__)
app.register_blueprint(agent_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(review_bp)


@app.route("/")
def index():
    return redirect("/dashboard")


@app.route("/api/scenarios")
def api_scenarios():
    """Lets the dashboard fire pre-built demo scenarios with one click."""
    return jsonify(SCENARIOS)


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok", "service": "TrustLedger-AI"})


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("[TrustLedger-AI] No database found -- run `python database/seed_data.py` first!")
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
