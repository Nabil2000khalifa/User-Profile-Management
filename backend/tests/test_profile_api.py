import asyncio
from datetime import date, datetime

import httpx
import pytest
from sqlalchemy.exc import IntegrityError

from app.api.profiles import create_profile, list_profiles, save_profile
from app.main import app
from app.models import UserProfile
from app.schemas.profile import ProfileCreateRequest


async def request_without_authentication() -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get("/api/v1/profiles")


def test_profile_list_requires_authentication() -> None:
    response = asyncio.run(request_without_authentication())

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_duplicate_profile_email_returns_field_error() -> None:
    class DuplicateSession:
        def add(self, _profile: UserProfile) -> None:
            pass

        def flush(self) -> None:
            raise IntegrityError("INSERT", {}, Exception("duplicate"))

        def rollback(self) -> None:
            pass

    payload = ProfileCreateRequest(
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1),
        email="jane@example.com",
        country="US",
        city="Chicago",
    )

    with pytest.raises(Exception, match="duplicate_email"):
        create_profile(
            payload,
            (type("Admin", (), {"id": 1})(), type("Session", (), {})()),
            None,
            DuplicateSession(),
        )


def test_profile_save_keeps_display_email_and_uses_gmail_canonical_key() -> None:
    class CaptureSession:
        def __init__(self) -> None:
            self.profile = None
            self.audit = None

        def add(self, value) -> None:
            if isinstance(value, UserProfile):
                self.profile = value
            else:
                self.audit = value

        def flush(self) -> None:
            self.profile.id = 3

        def commit(self) -> None:
            pass

        def refresh(self, _profile) -> None:
            pass

    db = CaptureSession()
    payload = ProfileCreateRequest(
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1),
        email="Jane.Doe+team@gmail.com",
        country="US",
        city="Chicago",
    )

    profile = save_profile(db, payload, 1)

    assert profile.email == "Jane.Doe+team@gmail.com"
    assert profile.canonical_email == "janedoe@gmail.com"


def test_profile_list_returns_total_and_page_metadata() -> None:
    item = UserProfile(
        id=2,
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1),
        email="jane@example.com",
        canonical_email="jane@example.com",
        country="US",
        city="Chicago",
        created_by=1,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )

    class ListSession:
        def scalar(self, _query):
            return 21

        def scalars(self, _query):
            return type("Result", (), {"all": lambda self: [item]})()

    page = list_profiles(
        (type("Admin", (), {"id": 1})(), type("Session", (), {})()),
        ListSession(),
    )

    assert page.total == 21
    assert page.page == 1
    assert page.page_size == 20
    assert page.total_pages == 2
    assert page.items[0].id == 2
