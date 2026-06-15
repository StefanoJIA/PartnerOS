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

export type DailyDecisionQueueItem = {
  id: string
  title: string
  category: string
  priority: string
  severity: string
  owner: string | null
  due_date: string | null
  partner_focus: string | null
  product_focus: string[]
  customer_or_account: string | null
  readiness_impact: string[]
  risk: string
  reason: string
  next_action: string
  source_type: string
  source_id: string | null
  source_path: string
  depends_on_external_input: boolean
  needs_business_signoff: boolean
  needs_security_signoff: boolean
  needs_partner_feedback: boolean
  needs_staging_credentials: boolean
  affects_d9: boolean
  affects_pilot: boolean
  customer_safe_boundary: string | null
  handling: DailyQueueHandlingRecord | null
}

export type DailyQueueHandlingRecord = {
  id: string
  queue_item_id: string
  source_type: string
  source_id: string | null
  source_path: string
  title: string
  category: string
  priority: string
  partner_focus: string | null
  product_focus: string[]
  customer_or_account: string | null
  owner: string | null
  handling_status: string
  follow_up_date: string | null
  blocked_reason: string | null
  internal_note: string | null
  decision_summary: string | null
  last_action: string | null
  action_count: number
  handling_events: Array<Record<string, unknown>>
  created_at: string
  updated_at: string
}

export type DailyQueueHandlingUpdate = {
  queue_item_id: string
  source_type: string
  source_id: string | null
  source_path: string
  title: string
  category: string
  priority: string
  partner_focus: string | null
  product_focus: string[]
  customer_or_account: string | null
  action: string
  owner?: string | null
  handling_status?: string | null
  follow_up_date?: string | null
  blocked_reason?: string | null
  internal_note?: string | null
  decision_summary?: string | null
}

export type DailyDecisionQueue = {
  summary: {
    total: number
    p0: number
    p1: number
    staging_or_d9: number
    pilot: number
    external_input_required: number
    business_signoff_required: number
    security_signoff_required: number
    partner_feedback_required: number
    order_or_feedback_risk: number
    acknowledged: number
    in_progress: number
    blocked: number
    deferred: number
    waiting_external: number
    overdue_followups: number
    my_items: number
    status: string
    external_staging_state: string
  }
  items: DailyDecisionQueueItem[]
  safety: Record<string, boolean>
}

export async function fetchDailyDecisionQueue() {
  const { data } = await http.get<DailyDecisionQueue>('/dashboard/daily-decision-queue')
  return data
}

export async function updateDailyQueueHandling(payload: DailyQueueHandlingUpdate) {
  const { data } = await http.patch<DailyQueueHandlingRecord>('/dashboard/daily-decision-queue/handling', payload)
  return data
}

export async function fetchDailyQueueHandling(params?: {
  source_type?: string
  source_id?: string
  partner_focus?: string
  category?: string
}) {
  const { data } = await http.get<DailyQueueHandlingRecord[]>('/dashboard/daily-decision-queue/handling', { params })
  return data
}

export type BusinessExecution = {
  summary: {
    lifecycle_accounts: number
    active_opportunities: number
    quote_learning_items: number
    delivery_risks: number
    product_validation_items: number
    partner_investment_items: number
    executive_decisions: number
    status: string
    external_staging_state: string
  }
  account_lifecycle: Array<{
    account_key: string
    customer_name: string
    current_stage: string
    stage_order: number
    priority: string
    owner: string | null
    partner_focus: string | null
    product_focus: string[]
    source_counts: Record<string, number>
    active_paths: string[]
    open_blockers: string[]
    next_action: string
    decision_reason: string
    readiness_impact: string[]
    commercial_health: {
      health: string
      score: number
      business_focus: string
      primary_stage: string
      primary_source_type: string
      primary_source_id: string | null
      primary_path: string
      primary_risk: string | null
      next_best_action: string
      conversion_signal: string
      delivery_signal: string
      repeat_business_signal: string
      business_questions: string[]
      safety: Record<string, boolean>
    }
  }>
  lifecycle: Array<{
    id: string
    source_type: string
    source_id: string | null
    customer_name: string
    lifecycle_stage: string
    stage_order: number
    priority: string
    owner: string | null
    partner_focus: string | null
    product_focus: string[]
    current_signal: string
    next_action: string
    blocker: string | null
    readiness_impact: string[]
    path: string
  }>
  opportunities: Array<{
    id: string
    opportunity_name: string
    customer_or_segment: string | null
    partner_focus: string | null
    product_focus: string[]
    project_size: string
    decision_stage: string
    competitive_signal: string
    probability: number
    risk: string
    next_action: string
    path: string
    stage_gate: {
      health: string
      current_stage: string
      current_stage_label: string
      suggested_next_stage: string | null
      suggested_next_stage_label: string | null
      blocks_next_stage: boolean
      missing_inputs: string[]
      exit_criteria: string[]
      dimension_review_needs: string[]
      market_response_impacts: string[]
      quote_learning_impacts: string[]
      business_questions: string[]
      next_best_action: string
      safety: Record<string, boolean>
    }
  }>
  quotations: Array<{
    quote_id: string
    quote_number: string
    customer_name: string | null
    status: string
    version_count: number
    manual_sent: boolean
    follow_up_date: string | null
    product_focus: string[]
    outcome_signal: string
    learning_signal: string
    next_action: string
    path: string
    commercial_intelligence: {
      health: string
      score: number
      priority: string
      business_focus: string
      partner_focus: string
      product_focus: string[]
      missing_inputs: string[]
      captured_dimensions: string[]
      dimension_review_needs: string[]
      market_response_review_needed: boolean
      quote_learning_impacts: string[]
      readiness_impact: string[]
      next_best_action: string
      customer_safe_boundary: string
      safety: Record<string, boolean>
    }
  }>
  products: Array<{
    partner_focus: string
    product_focus: string[]
    dimensions: string[]
    validation_signal: string
    risk: string
    next_action: string
    source_path: string
  }>
  partners: Array<{
    partner_id: string
    partner_name: string
    product_coverage: string[]
    readiness_level: string
    delivery_ability: string
    risk_assessment: string
    next_action: string
    path: string
  }>
  delivery: Array<{
    order_id: string
    order_number: string
    customer_name: string | null
    lifecycle_stage: string
    risk_level: string
    production_signal: string
    shipment_signal: string
    feedback_signal: string
    repeat_business_risk: string
    next_action: string
    path: string
    fulfillment_intelligence: {
      health: string
      risk_level: string
      business_focus: string
      quote_commercial_health: string | null
      quote_business_focus: string | null
      quote_dimension_gaps: string[]
      quote_missing_inputs: string[]
      missing_operating_inputs: string[]
      readiness_impact: string[]
      next_best_action: string
      customer_safe_boundary: string
      safety: Record<string, boolean>
    }
  }>
  executive_decisions: Array<{
    decision_id: string
    question: string
    answer: string
    priority: string
    owner: string
    next_action: string
    path: string
  }>
  safety: Record<string, boolean>
}

export async function fetchBusinessExecution() {
  const { data } = await http.get<BusinessExecution>('/dashboard/business-execution')
  return data
}
