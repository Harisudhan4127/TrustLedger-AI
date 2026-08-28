"""Minimal authentication helpers used by Module 3 (Verify agent identity and
active role). Uses simple hashed bearer tokens for the hackathon prototype --
JWTs are supported too (issue_jwt/verify_jwt) as the production-leaning path.
"""

import hashlib
import os

import jwt

JWT_SECRET = os.environ.get("JWT_SECRET", "trustledger-hackathon-demo-secret-change-me")
JWT_ALGO = "HS256"


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def verify_bearer_token(raw_token: str, stored_hash: str) -> bool:
    return hash_token(raw_token) == stored_hash


def issue_jwt(agent_id: str, role_id: str) -> str:
    return jwt.encode({"agent_id": agent_id, "role_id": role_id}, JWT_SECRET, algorithm=JWT_ALGO)


def verify_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        return None
