import sys
from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
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


def change_admin_password(
    db: Session,
    admin_email: str,
    current_password: str,
    new_password: str,
) -> Admin:
    if not current_password or not new_password:
        raise ValueError("Current and new passwords are required")
    admin = db.scalar(
        select(Admin).where(Admin.normalized_email == validate_email(admin_email))
    )
    if admin is None:
        raise LookupError("No administrator was found for that email")
    if not verify_password(admin.password_hash, current_password):
        raise PermissionError("The current password is incorrect")

    admin.password_hash = hash_password(new_password)
    record_audit(
        db,
        AuditEvent(
            admin_id=admin.id,
            action="ADMIN_PASSWORD_CHANGE",
            entity_type="admin",
            entity_id=admin.id,
        ),
    )
    db.commit()
    return admin


def main() -> int:
    admin_email = input("Admin email: ")
    current_password = getpass("Current password: ")
    new_password = getpass("New password: ")
    confirmation = getpass("Confirm new password: ")
    if new_password != confirmation:
        print("New passwords do not match", file=sys.stderr)
        return 2
    try:
        settings = get_settings()
        with Session(get_configured_engine(settings)) as db:
            change_admin_password(
                db,
                admin_email,
                current_password,
                new_password,
            )
    except (LookupError, PermissionError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print("Admin password updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
