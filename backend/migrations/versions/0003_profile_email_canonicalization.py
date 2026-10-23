"""Store display and canonical profile email values.

Revision ID: 0003_profile_email_canonicalization
Revises: 0002_admin_sessions
"""
from collections import defaultdict
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

from app.services.profiles import canonicalize_profile_email

revision: str = "0003_profile_email"
down_revision: str | None = "0002_admin_sessions"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    columns = {column["name"] for column in inspect(connection).get_columns("user_profiles")}
    source_column = "normalized_email" if "normalized_email" in columns else "email"
    rows = connection.execute(
        sa.text(
            "SELECT id, normalized_email FROM user_profiles ORDER BY id"
            if source_column == "normalized_email"
            else "SELECT id, email FROM user_profiles ORDER BY id"
        )
    ).mappings()
    canonical_rows: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        canonical_rows[canonicalize_profile_email(row[source_column])].append(row["id"])
    collisions = {email: ids for email, ids in canonical_rows.items() if len(ids) > 1}
    if collisions:
        raise RuntimeError(
            "Profile email canonicalization found collisions. "
            f"Resolve profile IDs before applying this migration: {collisions}"
        )

    if "normalized_email" in columns:
        op.drop_index("uq_user_profiles_normalized_email", table_name="user_profiles")
        op.alter_column(
            "user_profiles",
            "normalized_email",
            new_column_name="email",
            existing_type=sa.String(320, collation="utf8mb4_0900_ai_ci"),
        )
    if "email" not in columns:
        op.add_column(
            "user_profiles",
            sa.Column("email", sa.String(320, collation="utf8mb4_0900_ai_ci"), nullable=True),
        )
    if "canonical_email" not in columns:
        op.add_column(
            "user_profiles",
            sa.Column(
                "canonical_email",
                sa.String(320, collation="utf8mb4_0900_ai_ci"),
                nullable=True,
            ),
        )
    for row in connection.execute(
        sa.text("SELECT id, email FROM user_profiles ORDER BY id")
    ).mappings():
        connection.execute(
            sa.text(
                "UPDATE user_profiles SET email = :email, canonical_email = :canonical_email "
                "WHERE id = :id"
            ),
            {
                "email": row["email"],
                "canonical_email": canonicalize_profile_email(row["email"]),
                "id": row["id"],
            },
        )
    op.alter_column(
        "user_profiles",
        "email",
        nullable=False,
        existing_type=sa.String(320, collation="utf8mb4_0900_ai_ci"),
    )
    op.alter_column(
        "user_profiles",
        "canonical_email",
        nullable=False,
        existing_type=sa.String(320, collation="utf8mb4_0900_ai_ci"),
    )
    if "normalized_email" in columns:
        op.drop_index("uq_user_profiles_normalized_email", table_name="user_profiles")
        op.drop_column("user_profiles", "normalized_email")
    index_names = {index["name"] for index in inspect(connection).get_indexes("user_profiles")}
    if "uq_user_profiles_canonical_email" not in index_names:
        op.create_index(
            "uq_user_profiles_canonical_email",
            "user_profiles",
            ["canonical_email"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_index("uq_user_profiles_canonical_email", table_name="user_profiles")
    op.drop_column("user_profiles", "canonical_email")
    op.add_column(
        "user_profiles",
        sa.Column(
            "normalized_email",
            sa.String(320, collation="utf8mb4_0900_ai_ci"),
            nullable=True,
        ),
    )
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE user_profiles SET normalized_email = email")
    )
    op.alter_column(
        "user_profiles",
        "normalized_email",
        nullable=False,
        existing_type=sa.String(320, collation="utf8mb4_0900_ai_ci"),
    )
    op.drop_column("user_profiles", "email")
    op.create_index(
        "uq_user_profiles_normalized_email",
        "user_profiles",
        ["normalized_email"],
        unique=True,
    )
