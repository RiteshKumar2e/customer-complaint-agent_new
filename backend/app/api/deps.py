"""
Authentication and authorization dependencies.

Every protected route depends on `get_current_user` (or one of the role
helpers). Identity comes only from a valid, unrevoked access token; the role is
read from the database on each request, so a role change or deactivation takes
effect immediately and a forged/stale `role` claim grants nothing.
"""
from __future__ import annotations

from typing import Callable, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import forbidden, unauthorized
from app.core.security import AccessClaims, TokenError, decode_access_token
from app.db.database import get_db
from app.db.models import ROLE_ADMIN, ROLE_AGENT, ROLE_CUSTOMER, RevokedAccessToken, User

bearer_scheme = HTTPBearer(auto_error=False, description="Access token from /auth/login")


def get_token_claims(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> AccessClaims:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise unauthorized("Authentication required", "NOT_AUTHENTICATED")
    try:
        return decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise unauthorized(str(exc), exc.code)


def get_current_user(
    request: Request,
    claims: AccessClaims = Depends(get_token_claims),
    db: Session = Depends(get_db),
) -> User:
    if db.get(RevokedAccessToken, claims.jti) is not None:
        raise unauthorized("Session has ended. Please sign in again.", "TOKEN_REVOKED")
    user = db.get(User, claims.user_id)
    if user is None:
        raise unauthorized("Account not found", "INVALID_TOKEN")
    if user.token_version != claims.token_version:
        raise unauthorized("Session has ended. Please sign in again.", "TOKEN_REVOKED")
    if not user.is_active:
        raise forbidden("This account has been disabled.", "ACCOUNT_DISABLED")
    if not user.email_verified:
        raise forbidden("Verify your email address to continue.", "EMAIL_NOT_VERIFIED")
    request.state.user = user
    request.state.claims = claims
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    allowed = set(roles)

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise forbidden()
        return user

    return dependency


require_customer = require_roles(ROLE_CUSTOMER)
require_staff = require_roles(ROLE_AGENT, ROLE_ADMIN)
require_admin = require_roles(ROLE_ADMIN)
require_any_role = require_roles(ROLE_CUSTOMER, ROLE_AGENT, ROLE_ADMIN)
