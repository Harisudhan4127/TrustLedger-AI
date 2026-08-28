"""SQLite connection helper for TrustLedger-AI. Kept intentionally simple for a hackathon
prototype -- swap this module out for a PostgreSQL connection pool in production
without touching any of the modules/ or routes/ code, since they only import
get_db() / init_db() from here."""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "app.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"[TrustLedger-AI] Database initialised at {DB_PATH}")


if __name__ == "__main__":
    init_db()
