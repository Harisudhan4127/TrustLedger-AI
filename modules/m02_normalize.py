"""Module 2 -- Normalize and classify intended action.
Converts the raw intent (structured JSON, or a free-text instruction) into a
fixed ActionRequest schema every downstream module can rely on.
"""

import re

ACTION_KEYWORDS = {
    "transfer": ["transfer", "send", "pay"],
    "swap": ["swap", "exchange", "convert"],
    "stake": ["stake", "deposit into", "lock"],
    "payment": ["invoice", "payment for"],
}


def _classify_from_text(text: str) -> str:
    text_lower = text.lower()
    for action_type, keywords in ACTION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return action_type
    return "transfer"  # safe default for the prototype


def _extract_amount(text: str):
    match = re.search(r"(?:₹|rs\.?|inr)\s?([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def normalize(raw_payload: dict) -> dict:
    """Returns a normalized ActionRequest dict:
    {agent_id, action_type, amount, currency, destination, purpose, raw_instruction}
    """
    instruction = raw_payload.get("instruction", "")

    action_type = raw_payload.get("action_type") or _classify_from_text(instruction)
    amount = raw_payload.get("amount")
    if amount is None:
        amount = _extract_amount(instruction) or 0.0

    destination = raw_payload.get("destination") or raw_payload.get("counterparty_id")

    return {
        "agent_id": raw_payload.get("agent_id"),
        "action_type": action_type,
        "amount": float(amount),
        "currency": raw_payload.get("currency", "INR"),
        "destination": destination,
        "protocol": raw_payload.get("protocol"),
        "purpose": raw_payload.get("purpose", ""),
        "raw_instruction": instruction,
    }
