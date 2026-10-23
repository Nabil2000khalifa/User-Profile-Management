from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import digest_token, utc_now
from app.core.settings import Settings
from app.db.session import get_db_session
from app.models import Admin, AdminSession

SESSION_COOKIE = "admin_session"
CSRF_COOKIE = "admin_csrf"


class LoginThrottle:
    def __init__(self) -> None:
        self._attempts: dict[str, list[float]] = {}

    def allow(self, key: str, now: float, max_attempts: int, window_seconds: int) -> bool:
        attempts = [
            timestamp
            for timestamp in self._attempts.get(key, [])
            if now - timestamp < window_seconds
        ]
        if len(attempts) >= max_attempts:
            self._attempts[key] = attempts
            return False
        attempts.append(now)
        self._attempts[key] = attempts
        return True

    def clear(self, key: str) -> None:
        self._attempts.pop(key, None)


login_throttle = LoginThrottle()


def get_current_session(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> tuple[Admin, AdminSession]:
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    session = db.scalar(
        select(AdminSession)
        .where(
            AdminSession.token_hash == digest_token(raw_token),
            AdminSession.revoked_at.is_(None),
            AdminSession.expires_at > utc_now(),
        )
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    admin = db.get(Admin, session.admin_id)
    if admin is None or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    session.last_seen_at = utc_now()
    return admin, session


def require_csrf_token(
    request: Request,
    current_session: Annotated[tuple[Admin, AdminSession], Depends(get_current_session)],
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> None:
    _admin, session = current_session
    cookie_token = request.cookies.get(CSRF_COOKIE)
    if (
        not cookie_token
        or not csrf_header
        or not hmac.compare_digest(cookie_token, csrf_header)
        or not hmac.compare_digest(digest_token(csrf_header), session.csrf_token_hash)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


def set_auth_cookies(
    response: Response,
    session_token: str,
    csrf_token: str,
    settings: Settings,
    max_age: int,
) -> None:
    cookie_options = {
        "httponly": True,
        "secure": settings.secure_cookies,
        "samesite": "strict",
        "max_age": max_age,
        "path": "/",
    }
    response.set_cookie(SESSION_COOKIE, session_token, **cookie_options)
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        httponly=False,
        secure=settings.secure_cookies,
        samesite="strict",
        max_age=max_age,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


CurrentAdmin = Annotated[tuple[Admin, AdminSession], Depends(get_current_session)]
CsrfProtected = Annotated[None, Depends(require_csrf_token)]
