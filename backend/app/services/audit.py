import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import AuditLog


@dataclass(frozen=True)
class AuditEvent:
    admin_id: int | None
    action: str
    entity_type: str
    entity_id: int | None = None
    request_id: str | None = None
    metadata: dict[str, str] | None = None


def record_audit(db: Session, event: AuditEvent) -> None:
    db.add(
        AuditLog(
            admin_id=event.admin_id,
            action=event.action,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            request_id=event.request_id,
            metadata_json=(
                json.dumps(event.metadata, separators=(",", ":"))
                if event.metadata
                else None
            ),
        )
    )
