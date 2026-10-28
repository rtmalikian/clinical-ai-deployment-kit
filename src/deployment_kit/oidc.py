"""OIDC JWT validation (HS256, stdlib) + FastAPI dependency pattern.

Production note: prefer RS256 with the IdP's JWKS in real deployments.
This module implements the validation *logic* — signature, issuer,
audience, expiry, not-before — with HS256 so it is fully testable
offline with locally generated tokens. Swapping in JWKS/RS256 means
replacing `verify_signature` only; claim checks stay identical.
"""
from __future__ import annotations
import base64, hashlib, hmac, json, time

def b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def make_hs256_token(claims: dict, secret: str, header: dict|None=None) -> str:
    header = header or {"alg":"HS256","typ":"JWT"}
    h=b64url_encode(json.dumps(header,separators=(",",":")).encode())
    p=b64url_encode(json.dumps(claims,separators=(",",":")).encode())
    sig=hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{b64url_encode(sig)}"

class TokenError(ValueError): pass

def verify_signature(token: str, secret: str) -> dict:
    parts=token.split(".")
    if len(parts)!=3: raise TokenError("token must have 3 segments")
    signing_input=f"{parts[0]}.{parts[1]}".encode()
    expected=hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    try: actual=b64url_decode(parts[2])
    except Exception as e: raise TokenError("bad signature encoding") from e
    if not hmac.compare_digest(expected, actual): raise TokenError("signature verification failed")
    try: return json.loads(b64url_decode(parts[1]))
    except Exception as e: raise TokenError("bad payload JSON") from e

def validate_oidc_token(token: str, secret: str, issuer: str, audience: str, now: float|None=None, leeway: int=60) -> dict:
    """Validate an OIDC ID/access token. Returns claims or raises TokenError."""
    now = now or time.time()
    claims = verify_signature(token, secret)
    if claims.get("iss") != issuer: raise TokenError(f"issuer mismatch: {claims.get('iss')!r}")
    aud = claims.get("aud"); auds = aud if isinstance(aud, list) else [aud]
    if audience not in auds: raise TokenError("audience mismatch")
    if "exp" not in claims: raise TokenError("missing exp")
    if now > claims["exp"] + leeway: raise TokenError("token expired")
    if "nbf" in claims and now + leeway < claims["nbf"]: raise TokenError("token not yet valid")
    if not claims.get("sub"): raise TokenError("missing sub")
    return claims

ROLES = ("admin","clinician","coordinator","auditor","readonly")
RBAC = {
    "admin":       {"read","write","approve","manage_users","view_audit"},
    "clinician":   {"read","write","approve"},
    "coordinator": {"read","write"},
    "auditor":     {"read","view_audit"},
    "readonly":    {"read"},
}
def require_permission(claims: dict, permission: str) -> bool:
    roles = claims.get("roles") or ([claims["role"]] if claims.get("role") else [])
    return any(permission in RBAC.get(r,set()) for r in roles)
