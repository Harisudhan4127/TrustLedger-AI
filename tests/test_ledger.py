"""Ledger tamper-detection: verify_chain must catch a forged row and
pass an untouched chain. Uses the REAL modules/m13_ledger.
"""
import os
import tempfile
import unittest

import database.db as dbm
import database.seed_data as sd
from modules.m13_ledger import verify_chain
from modules.pipeline import run_pipeline
from utils.scenarios import SCENARIOS


class LedgerTamperDetected(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls._tmpdb = os.path.join(cls._tmp.name, "tl_ledger.db")
        cls._orig_path = dbm.DB_PATH
        dbm.DB_PATH = cls._tmpdb
        dbm.init_db()
        sd.seed()
        sc = SCENARIOS["scenario_1_normal"]
        run_pipeline(sc["payload"], sc["token"])

    @classmethod
    def tearDownClass(cls):
        dbm.DB_PATH = cls._orig_path
        cls._tmp.cleanup()

    def test_untouched_chain_verifies(self):
        conn = dbm.get_db()
        self.assertTrue(verify_chain(conn))
        conn.close()

    def test_tampered_row_fails_verification(self):
        conn = dbm.get_db()
        conn.execute("UPDATE audit_log SET entry_json='{}' WHERE log_id=(SELECT MAX(log_id) FROM audit_log)")
        conn.commit()
        self.assertFalse(verify_chain(conn))
        conn.close()


if __name__ == "__main__":
    unittest.main()
