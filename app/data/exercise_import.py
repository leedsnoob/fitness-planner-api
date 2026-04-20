from collections.abc import Sequence

from sqlalchemy import select

from app.db.session import get_session_factory
from app.models.exercise import Exercise


def import_exercises(records: Sequence[dict]) -> dict[str, int]:
    session_factory = get_session_factory()
    inserted = 0
    updated = 0

    with session_factory() as session:
        for record in records:
            existing = session.execute(
                select(Exercise).where(
                    Exercise.source_name == record["source_name"],
                    Exercise.source_id == record["source_id"],
                )
            ).scalar_one_or_none()

            if existing is None:
                session.add(Exercise(**record))
                inserted += 1
                continue

            for key, value in record.items():
                setattr(existing, key, value)
            updated += 1

        session.commit()

    return {"inserted": inserted, "updated": updated}
