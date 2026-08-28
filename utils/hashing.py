"""Hash-chaining helper for the immutable audit ledger (Module 13)."""

import hashlib
import json


def compute_entry_hash(prev_hash: str, entry_dict: dict) -> str:
    payload = (prev_hash or "GENESIS") + json.dumps(entry_dict, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
