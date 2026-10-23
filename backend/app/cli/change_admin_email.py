import sys

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.db.session import get_configured_engine
from app.models import Admin
from app.services.audit import AuditEvent, record_audit
from app.services.profiles import normalize_email


def validate_email(email: str) -> str:
    normalized_email = normalize_email(email)
    try:
        return normalize_email(
            str(TypeAdapter(EmailStr).validate_python(normalized_email))
        )
    except ValidationError as error:
        raise ValueError("A valid email address is required") from error


def change_admin_email(
    db: Session,
    current_email: str,
    new_email: str,
) -> Admin:
    normalized_current_email = validate_email(current_email)
    normalized_new_email = validate_email(new_email)
    admin = db.scalar(
        select(Admin).where(Admin.normalized_email == normalized_current_email)
    )
    if admin is None:
        raise LookupError("No administrator was found for the current email")
    if normalized_current_email == normalized_new_email:
        raise ValueError("The new email must be different from the current email")

    duplicate = db.scalar(
        select(Admin).where(
            Admin.normalized_email == normalized_new_email,
            Admin.id != admin.id,
        )
    )
    if duplicate is not None:
        raise RuntimeError("That email address is already used by another administrator")

    admin.normalized_email = normalized_new_email
    record_audit(
        db,
        AuditEvent(
            admin_id=admin.id,
            action="ADMIN_EMAIL_CHANGE",
            entity_type="admin",
            entity_id=admin.id,
        ),
    )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise RuntimeError("That email address is already used by another administrator") from error
    return admin


def main() -> int:
    current_email = input("Current admin email: ")
    new_email = input("New admin email: ")
    confirmation = input("Type CHANGE to confirm this email change: ")
    if confirmation != "CHANGE":
        print("Email change cancelled.", file=sys.stderr)
        return 2
    try:
        settings = get_settings()
        with Session(get_configured_engine(settings)) as db:
            change_admin_email(db, current_email, new_email)
    except (LookupError, RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print("Admin email updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
