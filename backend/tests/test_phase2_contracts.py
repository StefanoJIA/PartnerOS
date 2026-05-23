"""Contract checks for Phase 2 schemas (no DB required)."""

from app.schemas.dashboard_actions import DashboardActionsOut
from app.schemas.lead_workspace import LeadWorkspaceOut
from app.schemas.tasks_summary import TaskStatsOut


def test_dashboard_actions_has_expected_keys():
    fields = set(DashboardActionsOut.model_fields.keys())
    required = {
        "due_today_tasks",
        "overdue_tasks",
        "this_week_tasks",
        "leads_follow_up_due_today",
        "hot_leads",
        "leads_needing_follow_up",
        "leads_recent_activity",
        "leads_waiting_next_step",
        "rfqs_waiting_partner_quote",
        "rfqs_customer_reviewing",
        "rfqs_negotiating",
        "samples_requested",
        "samples_shipped",
        "samples_delivered_no_feedback",
        "samples_follow_up_due",
        "orders_delayed_milestones",
        "high_risk_orders",
        "orders_eta_missing",
        "orders_eta_passed_not_delivered",
        "recent_ai_outputs",
        "recommended_actions",
    }
    assert required <= fields


def test_lead_workspace_schema_fields():
    assert "related_rfqs" in LeadWorkspaceOut.model_fields
    assert "open_tasks" in LeadWorkspaceOut.model_fields


def test_task_stats_schema():
    assert set(TaskStatsOut.model_fields.keys()) >= {
        "due_today",
        "overdue",
        "this_week",
        "open_tasks",
        "completed_tasks",
    }
