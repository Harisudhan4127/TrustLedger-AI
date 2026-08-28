-- TrustLedger-AI database schema (SQLite). See PROJECT_DOCUMENTATION.md Part 14 for design notes.

CREATE TABLE IF NOT EXISTS roles (
    role_id TEXT PRIMARY KEY,
    role_name TEXT NOT NULL,
    allowed_action_types TEXT NOT NULL   -- JSON list
);

CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role_id TEXT NOT NULL,
    api_token_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE TABLE IF NOT EXISTS policies (
    policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id TEXT NOT NULL,
    max_single_txn REAL NOT NULL,
    daily_limit REAL NOT NULL,
    max_frequency_per_day INTEGER NOT NULL,
    allowed_counterparties TEXT,          -- JSON list ("*" = any whitelisted-tier)
    allowed_protocols TEXT,               -- JSON list
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE TABLE IF NOT EXISTS counterparties (
    counterparty_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    risk_tier TEXT NOT NULL,              -- whitelisted_known / known_new_pattern / unknown_unverified / flagged_blacklisted
    protocol TEXT,
    protocol_risk_tier TEXT,              -- audited_established / audited_new / unaudited
    first_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    txn_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    counterparty_id TEXT,
    protocol TEXT,
    raw_instruction TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    txn_id TEXT NOT NULL,
    amount_risk REAL,
    frequency_risk REAL,
    counterparty_risk REAL,
    protocol_risk REAL,
    market_risk REAL,
    behaviour_deviation REAL,
    manipulation_score REAL,
    risk_score REAL,
    evidence_json TEXT,
    FOREIGN KEY (txn_id) REFERENCES transactions(txn_id)
);

CREATE TABLE IF NOT EXISTS behaviour_profiles (
    agent_id TEXT PRIMARY KEY,
    mean_amount REAL DEFAULT 0,
    std_amount REAL DEFAULT 1,
    sample_count INTEGER DEFAULT 0,
    typical_counterparties TEXT DEFAULT '[]',
    last_updated TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    txn_id TEXT NOT NULL,
    decision TEXT NOT NULL,      -- EXECUTE / CONSTRAIN / ESCALATE / BLOCK
    reason TEXT,
    reviewed_by TEXT,
    review_status TEXT DEFAULT NULL,   -- pending / approved / modified / rejected (for ESCALATE)
    decided_at TEXT NOT NULL,
    FOREIGN KEY (txn_id) REFERENCES transactions(txn_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    txn_id TEXT,
    entry_json TEXT NOT NULL,
    prev_hash TEXT,
    entry_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
    txn_id TEXT,
    agent_id TEXT,
    incident_type TEXT NOT NULL,   -- policy_violation / manipulation_detected / drift_alert
    details TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS financial_state (
    agent_id TEXT PRIMARY KEY,
    daily_spent REAL DEFAULT 0,
    txn_count_today REAL DEFAULT 0,
    window_start TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
