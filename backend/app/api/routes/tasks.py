from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.object_type_http import parse_object_type_path
from app.models import Task, User
from app.schemas.crm import TaskCreate, TaskOut, TaskUpdate
from app.schemas.pagination import PaginatedResponse
from app.schemas.tasks_summary import TaskStatsOut
from app.services.activity import log_activity

router = APIRouter(prefix="/tasks", tags=["tasks"])
object_tasks_router = APIRouter(prefix="/objects", tags=["tasks"])


def _task_row_out(row: Task, assignee_email: str | None = None) -> TaskOut:
    return TaskOut(
        id=row.id,
        title=row.title,
        description=row.description,
        status=row.status,
        priority=row.priority,
        due_at=row.due_at,
        completed_at=row.completed_at,
        assignee_user_id=row.assignee_user_id,
        assignee_email=assignee_email,
        related_object_type=row.related_object_type,
        related_object_id=row.related_object_id,
        created_at=row.created_at,
    )


def _load_assignee_map(db: Session, tasks: list[Task]) -> dict[UUID, str]:
    ids = {t.assignee_user_id for t in tasks if t.assignee_user_id}
    if not ids:
        return {}
    rows = db.query(User.id, User.email).filter(User.id.in_(ids)).all()
    return {uid: email for uid, email in rows}


@router.get("/summary", response_model=TaskStatsOut)
def task_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TaskStatsOut:
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    tomorrow = today_start + timedelta(days=1)
    week_start_date = now.date() - timedelta(days=now.weekday())
    week_start = datetime.combine(week_start_date, datetime.min.time()).replace(tzinfo=timezone.utc)

    base_open = db.query(Task).filter(Task.is_active.is_(True), Task.status != "done")
    due_today = (
        base_open.filter(Task.due_at.isnot(None), Task.due_at >= today_start, Task.due_at < tomorrow).count()
    )
    overdue = base_open.filter(Task.due_at.isnot(None), Task.due_at < now).count()
    this_week = base_open.filter(
        Task.due_at.isnot(None),
        Task.due_at >= week_start,
        Task.due_at < week_start + timedelta(days=7),
    ).count()
    open_tasks = db.query(Task).filter(Task.is_active.is_(True), Task.status != "done").count()
    completed_tasks = db.query(Task).filter(Task.is_active.is_(True), Task.status == "done").count()
    return TaskStatsOut(
        due_today=int(due_today or 0),
        overdue=int(overdue or 0),
        this_week=int(this_week or 0),
        open_tasks=int(open_tasks or 0),
        completed_tasks=int(completed_tasks or 0),
    )


def _apply_task_filters(
    q,
    *,
    status_filter: str | None,
    priority: str | None,
    assignee_user_id: UUID | None,
    related_object_type: str | None,
    due_from: datetime | None,
    due_to: datetime | None,
    overdue: bool | None,
    due_today: bool | None,
    this_week: bool | None,
    search: str | None,
    now: datetime,
    today_start: datetime,
    tomorrow: datetime,
    week_start: datetime,
    week_end: datetime,
):
    if status_filter:
        q = q.filter(Task.status == status_filter)
    if priority:
        q = q.filter(Task.priority == priority)
    if assignee_user_id:
        q = q.filter(Task.assignee_user_id == assignee_user_id)
    if related_object_type:
        ot = parse_object_type_path(related_object_type)
        q = q.filter(Task.related_object_type == ot)
    if due_from:
        q = q.filter(Task.due_at.isnot(None), Task.due_at >= due_from)
    if due_to:
        q = q.filter(Task.due_at.isnot(None), Task.due_at <= due_to)
    if overdue:
        q = q.filter(Task.due_at.isnot(None), Task.due_at < now, Task.status != "done")
    if due_today:
        q = q.filter(Task.due_at.isnot(None), Task.due_at >= today_start, Task.due_at < tomorrow)
    if this_week:
        q = q.filter(Task.due_at.isnot(None), Task.due_at >= week_start, Task.due_at < week_end)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Task.title.ilike(like), Task.description.ilike(like)))
    return q


def _order_tasks(q, sort: str):
    pl = func.lower(func.coalesce(Task.priority, ""))
    prio = case(
        (pl == "high", 3),
        (pl == "medium", 2),
        (pl == "low", 1),
        else_=0,
    )
    if sort == "priority_desc,bin":
        return q.order_by(prio.desc(), Task.due_at.asc().nullslast())
    if sort == "created_at_desc":
        return q.order_by(Task.created_at.desc())
    if sort == "due_at_desc":
        return q.order_by(Task.due_at.desc().nullslast())
    # default due_at asc
    return q.order_by(Task.due_at.asc().nullslast(), prio.desc())


@router.get("", response_model=PaginatedResponse[TaskOut])
def list_tasks(
    status: str | None = None,
    priority: str | None = None,
    assignee_user_id: UUID | None = None,
    related_object_type: str | None = None,
    due_from: datetime | None = None,
    due_to: datetime | None = None,
    overdue: bool | None = None,
    due_today_filter: bool | None = Query(None, alias="due_today"),
    this_week: bool | None = None,
    search: str | None = None,
    sort: str = Query(
        "due_at_asc",
        description="due_at_asc | due_at_desc | priority_desc | created_at_desc",
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[TaskOut]:
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    tomorrow = today_start + timedelta(days=1)
    week_start_date = now.date() - timedelta(days=now.weekday())
    week_start = datetime.combine(week_start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    week_end = week_start + timedelta(days=7)

    q = db.query(Task).filter(Task.is_active.is_(True))
    q = _apply_task_filters(
        q,
        status_filter=status,
        priority=priority,
        assignee_user_id=assignee_user_id,
        related_object_type=related_object_type,
        due_from=due_from,
        due_to=due_to,
        overdue=overdue,
        due_today=due_today_filter,
        this_week=this_week,
        search=search,
        now=now,
        today_start=today_start,
        tomorrow=tomorrow,
        week_start=week_start,
        week_end=week_end,
    )
    total = q.count()
    sort_key = sort
    if sort_key == "priority_desc":
        sort_key = "priority_desc,bin"
    q = _order_tasks(q, sort_key)
    rows = q.offset((page - 1) * limit).limit(limit).all()
    amap = _load_assignee_map(db, rows)
    items = [_task_row_out(r, amap.get(r.assignee_user_id) if r.assignee_user_id else None) for r in rows]
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskOut:
    data = body.model_dump()
    if data.get("related_object_type"):
        data["related_object_type"] = parse_object_type_path(data["related_object_type"])
    row = Task(**data, created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="task",
        object_id=row.id,
        action="task_created",
        actor_id=user.id,
        diff={
            "title": row.title,
            "related_object_type": row.related_object_type,
            "related_object_id": str(row.related_object_id) if row.related_object_id else None,
        },
    )
    if row.related_object_type and row.related_object_id:
        log_activity(
            db,
            object_type=row.related_object_type,
            object_id=row.related_object_id,
            action="task_created",
            actor_id=user.id,
            diff={"task_id": str(row.id)},
        )
    db.commit()
    email = None
    if row.assignee_user_id:
        u = db.query(User).filter(User.id == row.assignee_user_id).first()
        email = u.email if u else None
    return _task_row_out(row, email)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TaskOut:
    row = db.query(Task).filter(Task.id == task_id, Task.is_active.is_(True)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    email = None
    if row.assignee_user_id:
        u = db.query(User).filter(User.id == row.assignee_user_id).first()
        email = u.email if u else None
    return _task_row_out(row, email)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: UUID,
    body: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskOut:
    row = db.query(Task).filter(Task.id == task_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    data = body.model_dump(exclude_unset=True)
    if "related_object_type" in data and data["related_object_type"] is not None:
        data["related_object_type"] = parse_object_type_path(data["related_object_type"])
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    email = None
    if row.assignee_user_id:
        u = db.query(User).filter(User.id == row.assignee_user_id).first()
        email = u.email if u else None
    return _task_row_out(row, email)


@router.post("/{task_id}/complete", response_model=TaskOut)
def complete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TaskOut:
    row = db.query(Task).filter(Task.id == task_id, Task.is_active.is_(True)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    row.status = "done"
    row.completed_at = datetime.now(timezone.utc)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="task",
        object_id=row.id,
        action="task_completed",
        actor_id=user.id,
        diff={"completed_at": row.completed_at.isoformat()},
    )
    if row.related_object_type and row.related_object_id:
        log_activity(
            db,
            object_type=row.related_object_type,
            object_id=row.related_object_id,
            action="task_completed",
            actor_id=user.id,
            diff={"task_id": str(row.id)},
        )
    db.commit()
    email = None
    if row.assignee_user_id:
        u = db.query(User).filter(User.id == row.assignee_user_id).first()
        email = u.email if u else None
    return _task_row_out(row, email)


@object_tasks_router.get("/{object_type}/{object_id}/tasks", response_model=PaginatedResponse[TaskOut])
def list_tasks_for_object(
    object_type: str,
    object_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[TaskOut]:
    ot = parse_object_type_path(object_type)
    q = db.query(Task).filter(
        Task.is_active.is_(True),
        Task.related_object_type == ot,
        Task.related_object_id == object_id,
    )
    if status_filter:
        q = q.filter(Task.status == status_filter)
    total = q.count()
    rows = q.order_by(Task.due_at.asc().nullslast()).offset((page - 1) * limit).limit(limit).all()
    amap = _load_assignee_map(db, rows)
    items = [_task_row_out(r, amap.get(r.assignee_user_id) if r.assignee_user_id else None) for r in rows]
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)
