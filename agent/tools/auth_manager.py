"""Authentication configuration for targeting protected endpoints.

Credentials are obfuscated at rest using base64 + per-session key.
This is NOT encryption — it prevents casual exposure in plaintext logs.
"""

import base64
import hashlib
import json
import logging
import os

from .logs_helper import log_path, get_session_dir

logger = logging.getLogger(__name__)


def _auth_file() -> str:
    return log_path("auth.json")


def _session_key() -> bytes:
    """Derive a simple key from session dir name (not cryptographic, just obfuscation)."""
    session = get_session_dir() or "phantom-default"
    return hashlib.sha256(session.encode()).digest()[:16]


def _obfuscate(value: str) -> str:
    key = _session_key()
    data = value.encode("utf-8")
    # Simple XOR + base64 — prevents plaintext in logs, not real encryption
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.b64encode(xored).decode("ascii")


def _deobfuscate(encoded: str) -> str:
    key = _session_key()
    xored = base64.b64decode(encoded)
    data = bytes(b ^ key[i % len(key)] for i, b in enumerate(xored))
    return data.decode("utf-8")


def _load_auth() -> dict:
    path = _auth_file()
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load auth.json: %s", e)
    return {}


def _save_auth(data: dict):
    try:
        with open(_auth_file(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.error("Failed to save auth.json: %s", e)


def get_auth_headers(target: str = None) -> dict:
    """Return HTTP headers dict for the given target (or global auth)."""
    data = _load_auth()
    config = data.get(target) or data.get("_global")
    if not config:
        return {}

    auth_type = config.get("type", "")
    raw_value = config.get("value", "")

    # Deobfuscate if stored with obfuscation
    try:
        value = _deobfuscate(raw_value)
    except Exception:
        value = raw_value  # Fallback: old plaintext format

    if auth_type == "bearer":
        return {"Authorization": f"Bearer {value}"}
    elif auth_type == "basic":
        return {"Authorization": f"Basic {value}"}
    elif auth_type == "cookie":
        return {"Cookie": value}
    elif auth_type == "header":
        # value format: "Header-Name: header-value"
        if ":" in value:
            name, _, val = value.partition(":")
            return {name.strip(): val.strip()}
    return {}


def run(auth_type: str, value: str, target: str = "") -> str:
    if auth_type not in ("bearer", "basic", "cookie", "header"):
        return "Unknown auth_type. Use: bearer, basic, cookie, header"

    data = _load_auth()
    key = target if target else "_global"
    data[key] = {"type": auth_type, "value": _obfuscate(value)}
    _save_auth(data)

    scope = f"target '{target}'" if target else "all targets (global)"
    # Log type but NOT the actual credential value
    logger.info("Auth configured: %s for %s", auth_type, scope)
    return f"Auth configured: {auth_type} for {scope}. Stored in session auth.json (obfuscated)."


TOOL_SPEC = {
    "name": "configure_auth",
    "description": (
        "Configure authentication for protected targets. "
        "Supports bearer tokens, basic auth, cookies, and custom headers. "
        "Other tools will automatically use these credentials."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "auth_type": {
                "type": "string",
                "description": "Auth type: bearer, basic, cookie, header",
            },
            "value": {
                "type": "string",
                "description": "Auth value (token, base64 creds, cookie string, or 'Header-Name: value')",
            },
            "target": {
                "type": "string",
                "description": "Target domain (leave empty for global auth)",
            },
        },
        "required": ["auth_type", "value"],
    },
}
