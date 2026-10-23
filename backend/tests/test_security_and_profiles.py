from datetime import date, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.auth import LoginThrottle, require_csrf_token
from app.core.security import digest_token, hash_password, verify_password
from app.schemas.profile import ProfileCreateRequest, ProfilePage, ProfileResponse
from app.services.profiles import (
    canonicalize_profile_email,
    normalize_email,
    validate_date_of_birth,
    validate_profile_location,
)


def test_password_hashing_uses_verifiable_argon2_hash() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash.startswith("$argon2id$")
    assert verify_password(password_hash, "correct horse battery staple")
    assert not verify_password(password_hash, "wrong password")


def test_session_csrf_requires_matching_cookie_header_and_session_hash() -> None:
    csrf_token = "csrf-token"
    request = SimpleNamespace(cookies={"admin_csrf": csrf_token})
    current_session = (SimpleNamespace(), SimpleNamespace(csrf_token_hash=digest_token(csrf_token)))

    require_csrf_token(request, current_session, csrf_token)

    with pytest.raises(Exception, match="CSRF validation failed"):
        require_csrf_token(request, current_session, "different")

    with pytest.raises(Exception, match="CSRF validation failed"):
        require_csrf_token(SimpleNamespace(cookies={}), current_session, csrf_token)

    with pytest.raises(Exception, match="CSRF validation failed"):
        require_csrf_token(request, current_session, None)


def test_login_throttle_blocks_after_configured_attempts() -> None:
    throttle = LoginThrottle()

    assert throttle.allow("client", 0, 2, 60)
    assert throttle.allow("client", 1, 2, 60)
    assert not throttle.allow("client", 2, 2, 60)
    assert throttle.allow("client", 61, 2, 60)


def test_profile_validation_rejects_invalid_location_and_future_dob() -> None:
    with pytest.raises(ValueError, match="approved"):
        validate_profile_location("US", "Mumbai")
    with pytest.raises(ValueError, match="future"):
        validate_date_of_birth(date(2030, 1, 1), date(2026, 1, 1))
    with pytest.raises(ValueError, match="1900-01-01"):
        validate_date_of_birth(date(1, 1, 1), date(2026, 1, 1))
    validate_date_of_birth(date(1900, 1, 1), date(2026, 1, 1))


def test_profile_schema_requires_all_fields_and_valid_email() -> None:
    with pytest.raises(ValidationError):
        ProfileCreateRequest(first_name="", last_name="Doe")

    profile = ProfileCreateRequest(
        first_name=" Jane ",
        last_name=" Doe ",
        date_of_birth=date(1990, 1, 1),
        email=" Jane.Doe@example.com ",
        country="US",
        city="Chicago",
    )

    assert profile.first_name == "Jane"
    assert profile.last_name == "Doe"
    assert normalize_email(str(profile.email)) == "jane.doe@example.com"


@pytest.mark.parametrize(
    ("email", "canonical"),
    [
        (" Jane.Doe@GMAIL.COM ", "janedoe@gmail.com"),
        ("jane.doe+intake@googlemail.com", "janedoe@gmail.com"),
        ("jane.doe@example.com", "jane.doe@example.com"),
        ("Jane.Doe@outlook.com", "jane.doe@outlook.com"),
        ("khalifanabil@gmail.com", "khalifanabil@gmail.com"),
        ("nabilkhalifa@gmail.com", "nabilkhalifa@gmail.com"),
    ],
)
def test_profile_email_canonicalization(email: str, canonical: str) -> None:
    assert canonicalize_profile_email(email) == canonical


def test_profile_page_reports_stable_pagination_metadata() -> None:
    item = ProfileResponse(
        id=1,
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1),
        email="jane@example.com",
        country="US",
        city="Chicago",
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )

    page = ProfilePage.from_items([item], page=2, page_size=20, total=21)

    assert page.page == 2
    assert page.page_size == 20
    assert page.total == 21
    assert page.total_pages == 2
    assert page.items[0].id == 1
