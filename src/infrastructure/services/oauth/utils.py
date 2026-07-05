import base64
import hashlib
import secrets


def generate_state_value() -> str:
    return secrets.token_urlsafe(32)


def generate_pkce_pair() -> tuple[str, str]:
    """Generates code_verifier and code_challenge for PKCE flow."""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge_bytes = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = (
        base64.urlsafe_b64encode(code_challenge_bytes).decode("ascii").rstrip("=")
    )
    return code_verifier, code_challenge
