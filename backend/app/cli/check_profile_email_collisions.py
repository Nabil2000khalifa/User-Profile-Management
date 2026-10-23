from collections import defaultdict

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.db.session import get_configured_engine
from app.services.profiles import canonicalize_profile_email


def find_collisions(db: Session) -> dict[str, list[int]]:
    collisions: dict[str, list[int]] = defaultdict(list)
    for row in db.execute(
        text("SELECT id, normalized_email FROM user_profiles ORDER BY id")
    ).mappings():
        collisions[canonicalize_profile_email(row["normalized_email"])].append(row["id"])
    return {email: ids for email, ids in collisions.items() if len(ids) > 1}


def main() -> int:
    settings = get_settings()
    with Session(get_configured_engine(settings)) as db:
        collisions = find_collisions(db)
    if collisions:
        print("Canonical email collisions require manual review:")
        for email, profile_ids in collisions.items():
            print(f"canonical_key={email} profile_ids={profile_ids}")
        return 1
    print("No canonical profile email collisions found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
