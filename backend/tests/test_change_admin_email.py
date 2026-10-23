from collections.abc import Iterator

import pytest
from sqlalchemy.exc import IntegrityError

from app.cli.change_admin_email import change_admin_email, main, validate_email
from app.models import Admin


class FakeSession:
    def __init__(self, results: Iterator[Admin | None]) -> None:
        self.results = iter(results)
        self.commits = 0
        self.rollbacks = 0
        self.added: list[object] = []

    def scalar(self, _query):
        return next(self.results)

    def add(self, value: object) -> None:
        self.added.append(value)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def test_validate_email_normalizes_and_validates() -> None:
    assert validate_email("  ADMIN@Example.com ") == "admin@example.com"


def test_change_admin_email_preserves_admin_and_records_audit() -> None:
    admin = Admin(
        id=7,
        normalized_email="admin@example.com",
        password_hash="argon2-hash",
        is_active=True,
    )
    db = FakeSession(iter([admin, None]))

    result = change_admin_email(db, " ADMIN@example.com ", " New@example.com ")

    assert result is admin
    assert admin.id == 7
    assert admin.normalized_email == "new@example.com"
    assert admin.password_hash == "argon2-hash"
    assert db.commits == 1
    assert len(db.added) == 1
    assert db.added[0].action == "ADMIN_EMAIL_CHANGE"
    assert db.added[0].metadata_json is None


def test_change_admin_email_rejects_missing_admin() -> None:
    db = FakeSession(iter([None]))

    with pytest.raises(LookupError, match="No administrator"):
        change_admin_email(db, "missing@example.com", "new@example.com")


def test_change_admin_email_rejects_duplicate_email() -> None:
    admin = Admin(id=7, normalized_email="admin@example.com", password_hash="hash")
    duplicate = Admin(id=8, normalized_email="new@example.com", password_hash="hash")
    db = FakeSession(iter([admin, duplicate]))

    with pytest.raises(RuntimeError, match="already used"):
        change_admin_email(db, "admin@example.com", "new@example.com")

    assert admin.normalized_email == "admin@example.com"
    assert db.commits == 0


def test_change_admin_email_rolls_back_a_race_lost_to_unique_constraint() -> None:
    admin = Admin(id=7, normalized_email="admin@example.com", password_hash="hash")
    db = FakeSession(iter([admin, None]))

    def commit() -> None:
        raise IntegrityError("duplicate", {}, Exception("duplicate"))

    db.commit = commit

    with pytest.raises(RuntimeError, match="already used"):
        change_admin_email(db, "admin@example.com", "new@example.com")

    assert db.rollbacks == 1


def test_main_requires_explicit_confirmation(monkeypatch) -> None:
    prompts = iter(["admin@example.com", "new@example.com", "no"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(prompts))

    assert main() == 2
