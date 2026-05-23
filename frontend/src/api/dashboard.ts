import { http } from '@/api/http'

export type RecommendedAction = {
  id: string
  title: string
  message: string
  severity: string
  object_type: string
  object_id: string
  path: string
}

export type TaskActionBrief = {
  id: string
  title: string
  status: string
  priority: string | null
  due_at: string | null
  assignee_email: string | null
  related_object_type: string | null
  related_object_id: string | null
}

export type LeadActionBrief = {
  id: string
  lead_name: string
  current_stage: string
  priority: string | null
}

export type DashboardActions = {
  due_today_tasks: TaskActionBrief[]
  overdue_tasks: TaskActionBrief[]
  this_week_tasks: TaskActionBrief[]
  leads_follow_up_due_today: LeadActionBrief[]
  hot_leads: LeadActionBrief[]
  leads_needing_follow_up: LeadActionBrief[]
  leads_recent_activity: LeadActionBrief[]
  leads_waiting_next_step: LeadActionBrief[]
  rfqs_waiting_partner_quote: { id: string; rfq_number: string; status: string }[]
  rfqs_customer_reviewing: { id: string; rfq_number: string; status: string }[]
  rfqs_negotiating: { id: string; rfq_number: string; status: string }[]
  samples_requested: { id: string; sample_request_number: string; sample_status: string }[]
  samples_shipped: { id: string; sample_request_number: string; sample_status: string }[]
  samples_delivered_no_feedback: { id: string; sample_request_number: string; sample_status?: string }[]
  samples_follow_up_due: { id: string; sample_request_number: string; sample_status: string; follow_up_due_date?: string | null }[]
  orders_delayed_milestones: {
    order_id: string
    order_number: string
    milestone_id: string
    milestone_name: string
  }[]
  high_risk_orders: { id: string; order_number: string; risk_level: string | null; target_delivery_date?: string | null }[]
  orders_eta_missing: { id: string; order_number: string; risk_level: string | null; target_delivery_date?: string | null }[]
  orders_eta_passed_not_delivered: { id: string; order_number: string; risk_level: string | null }[]
  recent_ai_outputs: { id: string; task_type: string; status: string; created_at: string }[]
  recommended_actions: RecommendedAction[]
}

export async function fetchDashboardActions() {
  const { data } = await http.get<DashboardActions>('/dashboard/actions')
  return data
}
