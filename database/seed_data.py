"""Seeds demo roles, agents, policies, and counterparties so the app is never
empty on first run. Prints the raw demo agent tokens once -- copy these for use
in your demo requests / utils/scenarios.py (they match what scenarios.py expects).

Run:  python database/seed_data.py
"""

import json
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db, init_db
from security.auth import hash_token

DEMO_TOKENS = {
    "AP_Payments_Agent_07": "demo-token-payments-07",
    "Treasury_Rebalancer_01": "demo-token-treasury-01",
    "DeFi_Yield_Agent_03": "demo-token-defi-03",
}


def seed():
    init_db()
    conn = get_db()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()

    # --- Roles -----------------------------------------------------------
    roles = [
        ("AP_Payments_Agent", "Accounts Payable Payments Agent", ["transfer", "payment"]),
        ("Treasury_Rebalancer", "Treasury Rebalancing Agent", ["transfer", "swap"]),
        ("DeFi_Yield_Agent", "DeFi Yield Optimisation Agent", ["stake", "swap"]),
    ]
    for role_id, role_name, actions in roles:
        cur.execute(
            "INSERT OR IGNORE INTO roles (role_id, role_name, allowed_action_types) VALUES (?,?,?)",
            (role_id, role_name, json.dumps(actions)),
        )

    # --- Policies ----------------------------------------------------------
    policies = [
        ("AP_Payments_Agent", 50000, 150000, 10, ["*whitelisted*"], []),
        ("Treasury_Rebalancer", 500000, 2000000, 5, ["*internal*"], ["approved_exchange"]),
        ("DeFi_Yield_Agent", 200000, 500000, 8, [], ["*whitelisted_protocol*"]),
    ]
    for role_id, max_single, daily, freq, cps, protos in policies:
        cur.execute(
            """INSERT INTO policies
               (role_id, max_single_txn, daily_limit, max_frequency_per_day,
                allowed_counterparties, allowed_protocols)
               VALUES (?,?,?,?,?,?)""",
            (role_id, max_single, daily, freq, json.dumps(cps), json.dumps(protos)),
        )

    # --- Agents --------------------------------------------------------------
    agents = [
        ("AP_Payments_Agent_07", "AP_Payments_Agent"),
        ("Treasury_Rebalancer_01", "Treasury_Rebalancer"),
        ("DeFi_Yield_Agent_03", "DeFi_Yield_Agent"),
    ]
    for agent_id, role_id in agents:
        token_hash = hash_token(DEMO_TOKENS[agent_id])
        cur.execute(
            """INSERT OR IGNORE INTO agents
               (agent_id, name, role_id, api_token_hash, status, created_at)
               VALUES (?,?,?,?,?,?)""",
            (agent_id, agent_id, role_id, token_hash, "active", now),
        )
        cur.execute(
            "INSERT OR IGNORE INTO behaviour_profiles (agent_id, mean_amount, std_amount, sample_count, last_updated) VALUES (?,?,?,?,?)",
            (agent_id, 9500, 4200, 12, now),
        )
        cur.execute(
            "INSERT OR IGNORE INTO financial_state (agent_id, daily_spent, txn_count_today, window_start) VALUES (?,?,?,?)",
            (agent_id, 0, 0, now),
        )

    # --- Counterparties -----------------------------------------------------
    counterparties = [
        ("Vendor_Kumar", "Approved Supplier - Kumar Traders", "whitelisted_known", None, None),
        ("Internal_Treasury_A", "Internal Treasury Account A", "whitelisted_known", None, None),
        ("Approved_Exchange_X", "Approved Exchange X", "whitelisted_known", "approved_exchange", "audited_established"),
        ("Whitelisted_Protocol_Y", "Whitelisted Yield Protocol Y", "whitelisted_known", "whitelisted_protocol", "audited_established"),
        ("Vendor_NewCo", "NewCo (never transacted before)", "unknown_unverified", None, "unaudited"),
        ("Wallet_Flagged_1", "Flagged wallet (deny-list)", "flagged_blacklisted", None, "unaudited"),
    ]
    for cp_id, name, tier, protocol, proto_tier in counterparties:
        cur.execute(
            """INSERT OR IGNORE INTO counterparties
               (counterparty_id, name, risk_tier, protocol, protocol_risk_tier, first_seen)
               VALUES (?,?,?,?,?,?)""",
            (cp_id, name, tier, protocol, proto_tier, now),
        )

    conn.commit()
    conn.close()

    print("[TrustLedger-AI] Seed data created.")
    print("[TrustLedger-AI] Demo agent tokens (use as Bearer tokens in /agent/intent):")
    for agent_id, token in DEMO_TOKENS.items():
        print(f"  {agent_id}: {token}")


if __name__ == "__main__":
    seed()
