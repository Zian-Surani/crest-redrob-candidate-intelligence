from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return f"{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_raw, expected_raw = stored.split("$", 1)
        salt = base64.urlsafe_b64decode(salt_raw.encode())
        expected = base64.urlsafe_b64decode(expected_raw.encode())
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return hmac.compare_digest(actual, expected)


def create_token(payload: dict[str, Any], secret: str, ttl_seconds: int) -> str:
    body = {**payload, "exp": int(time.time()) + ttl_seconds}
    encoded = base64.urlsafe_b64encode(
        json.dumps(body, separators=(",", ":")).encode()
    ).rstrip(b"=")
    signature = hmac.new(secret.encode(), encoded, hashlib.sha256).digest()
    return f"{encoded.decode()}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"


def decode_token(token: str, secret: str) -> dict[str, Any] | None:
    try:
        body_raw, signature_raw = token.split(".", 1)
        encoded = body_raw.encode()
        expected = hmac.new(secret.encode(), encoded, hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature_raw + "=" * (-len(signature_raw) % 4))
        if not hmac.compare_digest(expected, supplied):
            return None
        body = json.loads(base64.urlsafe_b64decode(body_raw + "=" * (-len(body_raw) % 4)))
        if int(body.get("exp", 0)) < int(time.time()):
            return None
        return body
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
