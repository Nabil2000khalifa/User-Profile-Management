import pytest

from app.cli.change_admin_password import change_admin_password, main
from app.core.security import hash_password, verify_password
from app.models import Admin


class FakeSession:
    def __init__(self, admin: Admin | None) -> None:
        self.admin = admin
        self.commits = 0
        self.added: list[object] = []

    def scalar(self, _query):
        return self.admin

    def add(self, value: object) -> None:
        self.added.append(value)

    def commit(self) -> None:
        self.commits += 1


def test_change_admin_password_replaces_hash_and_records_safe_audit() -> None:
    admin = Admin(
        id=7,
        normalized_email="admin@example.com",
        password_hash=hash_password("old password"),
    )
    db = FakeSession(admin)

    result = change_admin_password(
        db,
        " ADMIN@example.com ",
        "old password",
        "new password",
    )

    assert result is admin
    assert admin.id == 7
    assert verify_password(admin.password_hash, "new password")
    assert not verify_password(admin.password_hash, "old password")
    assert db.commits == 1
    assert len(db.added) == 1
    assert db.added[0].action == "ADMIN_PASSWORD_CHANGE"
    assert db.added[0].metadata_json is None


def test_change_admin_password_rejects_missing_admin() -> None:
    db = FakeSession(None)

    with pytest.raises(LookupError, match="No administrator"):
        change_admin_password(db, "missing@example.com", "old", "new")


def test_change_admin_password_rejects_incorrect_current_password() -> None:
    admin = Admin(
        id=7,
        normalized_email="admin@example.com",
        password_hash=hash_password("old password"),
    )
    db = FakeSession(admin)

    with pytest.raises(PermissionError, match="current password"):
        change_admin_password(db, "admin@example.com", "wrong", "new password")

    assert db.commits == 0


def test_change_admin_password_requires_passwords() -> None:
    admin = Admin(id=7, normalized_email="admin@example.com", password_hash="hash")

    with pytest.raises(ValueError, match="passwords are required"):
        change_admin_password(FakeSession(admin), "admin@example.com", "", "new")


def test_main_requires_matching_new_passwords(monkeypatch) -> None:
    inputs = iter(["admin@example.com"])
    passwords = iter(["old", "new", "different"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    monkeypatch.setattr("app.cli.change_admin_password.getpass", lambda _prompt: next(passwords))

    assert main() == 2
