"""Module 1 -- Financial Agent proposes Action Intent.
Entry point of the TrustLedger-AI security loop. Captures the raw request exactly as
submitted, before any interpretation happens.
"""

import uuid
from datetime import datetime


def capture_intent(payload: dict) -> dict:
    """Wrap the raw incoming request into a traceable Intent Event."""
    return {
        "request_id": f"REQ-{uuid.uuid4().hex[:8].upper()}",
        "received_at": datetime.utcnow().isoformat(),
        "raw_payload": payload,
    }
