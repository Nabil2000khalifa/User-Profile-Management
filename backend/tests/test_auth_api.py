from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Response

from app.api.auth import login
from app.core.auth import clear_auth_cookies, get_current_session, set_auth_cookies
from app.core.security import hash_password
from app.core.settings import Settings
from app.models import Admin, AdminSession
from app.schemas.auth import LoginRequest


class LoginSession:
    def __init__(self, admin: Admin) -> None:
        self.admin = admin
        self.added: list[object] = []
        self.active_session = AdminSession(admin_id=admin.id)

    def scalar(self, _query):
        return self.admin

    def scalars(self, _query):
        return type("Result", (), {"all": lambda _result: [self.active_session]})()

    def add(self, value) -> None:
        self.added.append(value)

    def commit(self) -> None:
        pass


def test_login_rotates_sessions_and_sets_auth_cookies() -> None:
    admin = Admin(
        id=7,
        normalized_email="admin@example.com",
        password_hash=hash_password("correct test password"),
        is_active=True,
    )
    db = LoginSession(admin)
    response = Response()
    settings = Settings(
        _env_file=None,
        database_url="mysql+pymysql://profile_app:secret@localhost:3306/user_profile_management",
        session_secret="test-session-secret",
    )

    result = login(
        LoginRequest(email="ADMIN@example.com", password="correct test password"),
        type("Request", (), {"client": type("Client", (), {"host": "127.0.0.1"})()})(),
        response,
        db,
        settings,
    )

    assert result.admin.id == 7
    assert result.admin.email == "admin@example.com"
    assert result.csrf_token
    assert db.active_session.revoked_at is not None
    assert any(isinstance(value, AdminSession) for value in db.added)
    assert "admin_session=" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]


def test_login_rejects_invalid_credentials_without_setting_cookies() -> None:
    class EmptySession:
        def scalar(self, _query):
            return None

        def add(self, _value) -> None:
            pass

        def commit(self) -> None:
            pass

    settings = Settings(
        _env_file=None,
        database_url="mysql+pymysql://localhost/user_profile_management",
        session_secret="test-session-secret",
    )

    with pytest.raises(HTTPException) as error:
        login(
            LoginRequest(email="missing@example.com", password="wrong"),
            SimpleNamespace(client=SimpleNamespace(host="127.0.0.1")),
            Response(),
            EmptySession(),
            settings,
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid email or password"


def test_auth_cookies_have_secure_attributes_and_logout_clears_both() -> None:
    settings = Settings(
        _env_file=None,
        app_env="staging",
        database_url="mysql+pymysql://localhost/user_profile_management",
        session_secret="test-session-secret",
    )
    response = Response()

    set_auth_cookies(response, "session-value", "csrf-value", settings, 3600)
    cookie_header = "; ".join(
        value.decode("latin-1")
        for name, value in response.raw_headers
        if name == b"set-cookie"
    )

    assert "admin_session=session-value" in cookie_header
    assert "admin_csrf=csrf-value" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "Secure" in cookie_header
    assert "SameSite=strict" in cookie_header
    assert "Max-Age=3600" in cookie_header

    clear_response = Response()
    clear_auth_cookies(clear_response)
    clear_cookie_header = "; ".join(
        value.decode("latin-1")
        for name, value in clear_response.raw_headers
        if name == b"set-cookie"
    )
    assert "admin_session=" in clear_cookie_header
    assert "admin_csrf=" in clear_cookie_header


def test_current_session_requires_cookie_and_rejects_unknown_session() -> None:
    class EmptySession:
        def scalar(self, _query):
            return None

        def get(self, _model, _identifier):
            return None

    with pytest.raises(HTTPException) as missing_cookie:
        get_current_session(SimpleNamespace(cookies={}), EmptySession())
    assert missing_cookie.value.status_code == 401

    with pytest.raises(HTTPException) as unknown_cookie:
        get_current_session(
            SimpleNamespace(cookies={"admin_session": "opaque-value"}),
            EmptySession(),
        )
    assert unknown_cookie.value.status_code == 401
