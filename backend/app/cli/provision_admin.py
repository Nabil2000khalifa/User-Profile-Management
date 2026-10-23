import sys
from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.settings import get_settings
from app.db.session import get_configured_engine
from app.models import Admin


def provision_admin(email: str, password: str) -> None:
    try:
        normalized_email = str(TypeAdapter(EmailStr).validate_python(email)).lower()
    except ValidationError as error:
        raise ValueError("A valid email address is required") from error
    if not normalized_email or not password:
        raise ValueError("Email and password are required")

    settings = get_settings()
    with Session(get_configured_engine(settings)) as db:
        if db.scalar(select(Admin.id).limit(1)) is not None:
            raise RuntimeError("An admin already exists; refusing to provision another admin")
        db.add(
            Admin(
                normalized_email=normalized_email,
                password_hash=hash_password(password),
            )
        )
        db.commit()


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m app.cli.provision_admin EMAIL", file=sys.stderr)
        return 2
    password = getpass("Password: ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match", file=sys.stderr)
        return 2
    try:
        provision_admin(sys.argv[1], password)
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print("Admin provisioned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
