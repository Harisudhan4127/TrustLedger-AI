"""Module 4 -- Detect prompt / instruction manipulation.
Two-layer approach: a fast rule/signature layer (this file), optionally
combined with the LLM semantic layer in ml/manipulation_llm.py (Part 7 /
Part 8 of the documentation). Returns a manipulation_score 0-100 plus the
specific flags that fired, so the reasoning is always explainable.
"""

OVERRIDE_PATTERNS = [
    "ignore your", "ignore previous", "ignore the policy", "disregard policy",
    "disregard your", "skip the usual checks", "skip verification",
    "don't wait for the usual checks", "no need to check", "bypass",
    "disable limit", "disable the limit", "maintenance mode",
]

URGENCY_PATTERNS = [
    "urgently", "immediately", "right now", "don't wait", "asap", "act now",
]

AUTHORITY_CLAIM_PATTERNS = [
    "ceo said", "cfo approved", "verbally approved", "trust me", "boss said",
]

NEW_DESTINATION_PATTERNS = [
    "new wallet", "new account", "different wallet", "this new wallet",
]


def _scan(text: str, patterns: list) -> list:
    text_lower = text.lower()
    return [p for p in patterns if p in text_lower]


def detect_manipulation(raw_instruction: str) -> dict:
    if not raw_instruction:
        return {"manipulation_score": 0, "flags": [], "reasoning": "No instruction text supplied."}

    override_hits = _scan(raw_instruction, OVERRIDE_PATTERNS)
    urgency_hits = _scan(raw_instruction, URGENCY_PATTERNS)
    authority_hits = _scan(raw_instruction, AUTHORITY_CLAIM_PATTERNS)
    destination_hits = _scan(raw_instruction, NEW_DESTINATION_PATTERNS)

    score = 0
    flags = []
    if override_hits:
        score += 60
        flags.append("instruction_override_attempt")
    if urgency_hits:
        score += 20
        flags.append("urgency_pressure")
    if authority_hits:
        score += 15
        flags.append("unverified_authority_claim")
    if destination_hits:
        score += 10
        flags.append("unusual_destination_request")

    score = min(score, 100)
    reasoning = (
        f"Matched patterns: {override_hits + urgency_hits + authority_hits + destination_hits}"
        if flags else "No manipulation signatures matched."
    )
    return {"manipulation_score": score, "flags": flags, "reasoning": reasoning}
