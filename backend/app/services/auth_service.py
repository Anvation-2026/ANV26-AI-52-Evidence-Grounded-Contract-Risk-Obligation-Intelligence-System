import base64
import hashlib
import hmac
import json
import os
import secrets
import time

TOKEN_TTL_SECONDS = 60 * 60 * 8
# Avoid a predictable signing key in local demos when AUTH_SECRET is omitted.
# The ephemeral key changes on restart; configure AUTH_SECRET for stable sessions.
_EPHEMERAL_SECRET = secrets.token_bytes(32)

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return "pbkdf2_sha256$310000$%s$%s" % (base64.urlsafe_b64encode(salt).decode(), base64.urlsafe_b64encode(derived).decode())

def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt_text, hash_text = stored.split("$", 3)
        if scheme != "pbkdf2_sha256": return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(hash_text.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def _secret() -> bytes:
    configured = os.getenv("AUTH_SECRET", "").strip()
    return configured.encode("utf-8") if configured else _EPHEMERAL_SECRET

def create_token(user_id: int, email: str, name: str) -> str:
    payload = {"sub": user_id, "email": email, "name": name, "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(hmac.new(_secret(), body.encode(), hashlib.sha256).digest()).decode().rstrip("=")
    return body + "." + signature

def decode_token(token: str):
    try:
        body, signature = token.split(".", 1)
        expected = base64.urlsafe_b64encode(hmac.new(_secret(), body.encode(), hashlib.sha256).digest()).decode().rstrip("=")
        if not hmac.compare_digest(signature, expected): return None
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if int(payload.get("exp", 0)) < int(time.time()): return None
        if not payload.get("sub") or not payload.get("email"): return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
