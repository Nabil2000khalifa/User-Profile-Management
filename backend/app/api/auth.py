import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import (
    CsrfProtected,
    CurrentAdmin,
    clear_auth_cookies,
    login_throttle,
    set_auth_cookies,
)
from app.core.security import (
    digest_token,
    new_opaque_token,
    session_expiry,
    utc_now,
    verify_password,
)
from app.core.settings import Settings, get_settings
from app.db.session import get_db_session
from app.models import Admin, AdminSession
from app.schemas.auth import AdminResponse, LoginRequest, LoginResponse
from app.services.audit import AuditEvent, record_audit
from app.services.profiles import normalize_email

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def request_key(request: Request, email: str) -> str:
    return f"{request.client.host if request.client else 'unknown'}:{email}"


def record_login_failure(db: Session, admin: Admin | None) -> None:
    record_audit(
        db,
        AuditEvent(
            admin_id=admin.id if admin else None,
            action="LOGIN_FAILURE",
            entity_type="admin",
        ),
    )
    db.commit()


def rotate_session(db: Session, admin: Admin, settings: Settings) -> tuple[str, str]:
    now = utc_now()
    active_sessions = db.scalars(
        select(AdminSession).where(
            AdminSession.admin_id == admin.id,
            AdminSession.revoked_at.is_(None),
        )
    ).all()
    for active_session in active_sessions:
        active_session.revoked_at = now
    session_token = new_opaque_token()
    csrf_token = new_opaque_token()
    db.add(
        AdminSession(
            admin_id=admin.id,
            token_hash=digest_token(session_token),
            csrf_token_hash=digest_token(csrf_token),
            expires_at=session_expiry(settings.session_ttl_hours, now),
        )
    )
    admin.last_login_at = now
    return session_token, csrf_token


def authenticate_admin(db: Session, email: str, password: str) -> Admin | None:
    admin = db.scalar(select(Admin).where(Admin.normalized_email == email))
    if admin is None or not admin.is_active:
        return None
    return admin if verify_password(admin.password_hash, password) else None


def complete_login(
    db: Session,
    admin: Admin,
    response: Response,
    settings: Settings,
) -> LoginResponse:
    session_token, csrf_token = rotate_session(db, admin, settings)
    record_audit(
        db,
        AuditEvent(admin_id=admin.id, action="LOGIN_SUCCESS", entity_type="admin"),
    )
    db.commit()
    set_auth_cookies(
        response,
        session_token,
        csrf_token,
        settings,
        settings.session_ttl_hours * 3600,
    )
    return LoginResponse(
        admin=AdminResponse(id=admin.id, email=admin.normalized_email),
        csrf_token=csrf_token,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    email = normalize_email(str(payload.email))
    throttle_key = request_key(request, email)
    if not login_throttle.allow(
        throttle_key,
        time.monotonic(),
        settings.login_max_attempts,
        settings.login_window_seconds,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts",
        )

    admin = authenticate_admin(db, email, payload.password)
    if admin is None:
        record_login_failure(db, admin)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    login_throttle.clear(throttle_key)
    return complete_login(db, admin, response, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    current_admin: CurrentAdmin,
    _csrf: CsrfProtected,
    db: Annotated[Session, Depends(get_db_session)],
) -> None:
    admin, session = current_admin
    session.revoked_at = utc_now()
    record_audit(
        db,
        AuditEvent(admin_id=admin.id, action="LOGOUT", entity_type="admin"),
    )
    db.commit()
    clear_auth_cookies(response)


@router.get("/me", response_model=AdminResponse)
def current_admin(current_admin: CurrentAdmin) -> AdminResponse:
    admin, _session = current_admin
    return AdminResponse(id=admin.id, email=admin.normalized_email)
