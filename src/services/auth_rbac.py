from typing import List, Optional

from fastapi import HTTPException

from ..db import SessionLocal
from ..db.models import Role, UserRole
from .auth import verify_token


def require_auth(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        claims = verify_token(token)
        return claims
    except Exception:
        raise HTTPException(401, "invalid token")


def roles_for_user(user_id: int) -> List[str]:
    with SessionLocal() as db:
        rows = (
            db.query(UserRole, Role)
            .join(Role, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        return [r.Role.name if hasattr(r, "Role") else r[1].name for r in rows]


def require_role(authorization: Optional[str], allowed: List[str]):
    claims = require_auth(authorization)
    uid = int(claims.get("sub"))
    user_roles = roles_for_user(uid)
    if "admin" in user_roles:
        return claims
    if not any(r in user_roles for r in allowed):
        raise HTTPException(403, f"requires role: {allowed}")
    return claims
