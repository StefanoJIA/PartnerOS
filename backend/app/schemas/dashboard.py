from pydantic import BaseModel


class DashboardSummary(BaseModel):
    new_leads_this_week: int
    hot_lead_ids: list[str]
    strategic_company_ids: list[str]
    overdue_task_ids: list[str]
    followup_due_lead_ids: list[str]
    open_rfqs: int
    open_samples: int
    active_orders: int
    partner_count: int
