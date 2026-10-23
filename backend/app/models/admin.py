from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.session import AdminSession
    from app.models.user_profile import UserProfile


class Admin(Base):
    __tablename__ = "admins"
    __table_args__ = (
        Index("uq_admins_normalized_email", "normalized_email", unique=True),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    normalized_email: Mapped[str] = mapped_column(
        String(320, collation="utf8mb4_0900_ai_ci"),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    profiles: Mapped[list[UserProfile]] = relationship(back_populates="created_by_admin")
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="admin")
    sessions: Mapped[list[AdminSession]] = relationship(back_populates="admin")
