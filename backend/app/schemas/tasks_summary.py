from pydantic import BaseModel


class TaskStatsOut(BaseModel):
    due_today: int
    overdue: int
    this_week: int
    open_tasks: int
    completed_tasks: int
