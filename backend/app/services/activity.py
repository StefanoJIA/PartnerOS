from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ActivityLog


def log_activity(
    db: Session,
    *,
    object_type: str,
    object_id: UUID,
    action: str,
    actor_id: UUID | None,
    diff: dict[str, Any] | None = None,
) -> None:
    entry = ActivityLog(
        object_type=object_type,
        object_id=object_id,
        action=action,
        actor_id=actor_id,
        diff=diff,
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(entry)
