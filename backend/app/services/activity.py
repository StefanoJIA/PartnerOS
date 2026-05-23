from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ActivityLog
from app.services.json_safe import serialize_for_json


def log_activity(
    db: Session,
    *,
    object_type: str,
    object_id: UUID,
    action: str,
    actor_id: UUID | None,
    diff: dict[str, Any] | None = None,
) -> None:
    safe_diff = serialize_for_json(diff) if diff is not None else None
    entry = ActivityLog(
        object_type=object_type,
        object_id=object_id,
        action=action,
        actor_id=actor_id,
        diff=safe_diff,
        created_by_id=actor_id,
        updated_by_id=actor_id,
    )
    db.add(entry)
