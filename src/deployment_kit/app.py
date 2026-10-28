"""FastAPI identity demo: OIDC-protected route + SCIM 2.0 provisioning stub.

SCIM is a *stub*: in-memory store, bearer-token check, Users CRUD per
RFC 7644 shape. It demonstrates the provisioning surface an enterprise
IdP (Okta/Azure AD) expects; it is not a production directory.
"""
from __future__ import annotations
import itertools, os
from .oidc import validate_oidc_token, require_permission, TokenError

try:
    from fastapi import FastAPI, Header, HTTPException, Request
    from fastapi.responses import JSONResponse
except ImportError:  # allows unit tests of pure logic without FastAPI installed
    FastAPI = None

SCIM_TOKEN = os.environ.get("SCIM_TOKEN", "dev-scim-token-change-me")
OIDC_SECRET = os.environ.get("OIDC_SECRET", "dev-secret-change-me")
OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "https://idp.example.org")
OIDC_AUDIENCE = os.environ.get("OIDC_AUDIENCE", "clinical-ai-app")

_users: dict[str, dict] = {}
_ids = itertools.count(1)

def scim_create_user(payload: dict) -> dict:
    if not payload.get("userName"): raise ValueError("userName required (SCIM core schema)")
    uid = f"scim-{next(_ids):04d}"
    user = {"id": uid, "userName": payload["userName"], "active": payload.get("active", True),
            "name": payload.get("name", {}), "emails": payload.get("emails", []),
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]}
    _users[uid] = user; return user

def scim_deprovision(user_id: str) -> dict:
    if user_id not in _users: raise KeyError(user_id)
    _users[user_id]["active"] = False; return _users[user_id]

def create_app():
    if FastAPI is None: raise RuntimeError("FastAPI not installed")
    app = FastAPI(title="Clinical AI Deployment Kit — Identity Demo")

    def auth(authorization: str|None):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "missing bearer token")
        try: return validate_oidc_token(authorization[7:], OIDC_SECRET, OIDC_ISSUER, OIDC_AUDIENCE)
        except TokenError as e: raise HTTPException(401, str(e))

    @app.get("/healthz")
    def healthz(): return {"ok": True}

    @app.get("/api/me")
    def me(authorization: str|None = Header(default=None)):
        claims = auth(authorization); return {"sub": claims["sub"], "roles": claims.get("roles", [])}

    @app.get("/api/audit")
    def audit(authorization: str|None = Header(default=None)):
        claims = auth(authorization)
        if not require_permission(claims, "view_audit"): raise HTTPException(403, "auditor/admin role required")
        return {"entries": []}

    @app.post("/scim/v2/Users", status_code=201)
    async def scim_post(request: Request, authorization: str|None = Header(default=None)):
        if authorization != f"Bearer {SCIM_TOKEN}": raise HTTPException(401, "bad SCIM token")
        try: return scim_create_user(await request.json())
        except ValueError as e: raise HTTPException(400, str(e))

    @app.patch("/scim/v2/Users/{user_id}")
    def scim_patch(user_id: str, authorization: str|None = Header(default=None)):
        if authorization != f"Bearer {SCIM_TOKEN}": raise HTTPException(401, "bad SCIM token")
        try: return scim_deprovision(user_id)
        except KeyError: raise HTTPException(404, "user not found")
    return app

if FastAPI is not None:
    app = create_app()
