from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.admin import Admin


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        Index(
            "uq_user_profiles_canonical_email",
            "canonical_email",
            unique=True,
        ),
        Index("ix_user_profiles_name", "last_name", "first_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    email: Mapped[str] = mapped_column(
        String(320, collation="utf8mb4_0900_ai_ci"),
        nullable=False,
    )
    canonical_email: Mapped[str] = mapped_column(
        String(320, collation="utf8mb4_0900_ai_ci"),
        nullable=False,
    )
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("admins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    created_by_admin: Mapped[Admin] = relationship(back_populates="profiles")
