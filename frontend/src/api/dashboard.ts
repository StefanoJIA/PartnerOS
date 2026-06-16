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
  decision_brief: string[]
  partner_rollup: DailyDecisionQueueRollup[]
  product_rollup: DailyDecisionQueueRollup[]
  category_rollup: DailyDecisionQueueRollup[]
  safety: Record<string, boolean>
}

export type DailyDecisionQueueRollup = {
  key: string
  label: string
  total: number
  p0: number
  p1: number
  affects_d9: number
  affects_pilot: number
  external_input_required: number
  top_priority: string
  top_next_action: string
  source_paths: string[]
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
    commercial_intelligence_items: number
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
    stage_progression?: {
      health: string
      current_stage: string
      next_stage: string | null
      blocks_next_stage: boolean
      missing_inputs: string[]
      recommended_action: string
      handoff_object: string
      recommended_entry_path: string
      readiness_impact: string[]
      why_now: string
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
      partner_fit_impacts?: string[]
      business_questions: string[]
      next_best_action: string
      safety: Record<string, boolean>
    }
    partner_fit?: {
      partner_id: string
      partner_name: string
      fit_score: number
      capability_score: number
      investment_priority: string
      business_focus: string
      matched_terms: string[]
      missing_inputs: string[]
      risk_signals: string[]
      readiness_impact: string[]
      next_best_action: string
      customer_safe_boundary: string
    }
    execution_context?: {
      health: string
      priority?: string
      linked_quote_count?: number
      linked_order_count?: number
      quote?: {
        quote_id: string
        quote_number: string
        status: string
        manual_sent: boolean
        follow_up_date: string | null
        version_count: number
        line_count: number
        path: string
      } | null
      orders?: Array<{
        order_id: string
        order_number: string
        status: string
        customer_name: string | null
        production_milestone_count: number
        shipment_plan_count: number
        path: string
      }>
      feedback?: {
        total: number
        open: number
        high_priority: number
        latest_ticket_number: string | null
        latest_status: string | null
        latest_priority: string | null
        path: string
      }
      delivery?: {
        order_id: string | null
        health: string | null
        risk_level: string | null
        business_focus: string | null
        missing_operating_inputs: string[]
        readiness_impact: string[]
        partner_execution_health: string | null
        next_best_action: string | null
      }
      market_response?: {
        recommendation_count: number
        quote_learning_count: number
      }
      conversion_signal?: {
        stage: string
        status: string
        manual_handoff_required: boolean
        next_best_action: string
      }
      missing_inputs?: string[]
      readiness_impact?: string[]
      next_best_action?: string
      customer_safe_boundary?: string
      safety?: Record<string, boolean>
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
    partner_readiness?: {
      health: string
      priority: string
      readiness_impact: string[]
      missing_inputs: string[]
      risk_signals: string[]
      next_best_action: string
      partners: Array<{
        partner_id: string
        partner_name: string
        readiness_score: number
        business_focus: string
        missing_inputs: string[]
        risk_signals: string[]
        next_best_action: string
      }>
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
    validation_context?: {
      health: string
      priority: string
      evidence_counts: {
        opportunities: number
        quotes: number
        orders: number
        feedback: number
        open_feedback: number
        high_priority_feedback: number
        delivery_risks: number
        market_reviews: number
        market_items: number
        customer_safe_reviews: number
      }
      source_paths: {
        opportunity: string | null
        quote: string | null
        order: string | null
        feedback: string | null
        market_response: string | null
      }
      dimensions_requiring_evidence: string[]
      readiness_impact: string[]
      next_best_action: string
      customer_safe_boundary: string
      safety: Record<string, boolean>
    }
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
    capability_intelligence: {
      health: string
      score: number
      investment_priority: string
      business_focus: string
      product_coverage: string[]
      capability_keys: string[]
      delivery_reliability: string
      rating_average: number | null
      historical_cooperation: Record<string, number>
      missing_inputs: string[]
      risk_signals: string[]
      readiness_impact: string[]
      next_best_action: string
      customer_safe_boundary: string
      safety: Record<string, boolean>
    }
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
      quote_partner_readiness_health?: string | null
      quote_dimension_gaps: string[]
      quote_missing_inputs: string[]
      missing_operating_inputs: string[]
      partner_execution_readiness?: {
        health: string
        priority: string
        next_best_action: string
        customer_safe_boundary: string
        missing_inputs: string[]
        risk_signals: string[]
        readiness_impact: string[]
        safety: Record<string, boolean>
        partners: Array<{
          partner_id: string
          partner_name: string
          quote_readiness_health: string | null
          handoff_stage: string
          readiness_score: number
          split_created: boolean
          split_id: string | null
          split_status: string | null
          supplier_confirmation_count: number
          production_milestone_count: number
          shipment_plan_count: number
          missing_execution_inputs: string[]
          risk_signals: string[]
          readiness_impact: string[]
          next_best_action: string
          customer_safe_boundary: string
        }>
      }
      readiness_impact: string[]
      next_best_action: string
      customer_safe_boundary: string
      safety: Record<string, boolean>
    }
  }>
  commercial_intelligence: {
    executive_summary: Record<string, unknown>
    win_loss: Array<Record<string, unknown>>
    customer_value: Array<Record<string, unknown>>
    partner_performance: Array<Record<string, unknown>>
    product_market_fit: Array<Record<string, unknown>>
    revenue_forecast: Record<string, unknown>
    account_360: Array<Record<string, unknown>>
  }
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

export interface WinLossIntelligenceDashboard {
  summary: {
    total: number
    won: number
    lost: number
    open_or_unclear: number
    win_rate: number | null
    commercial_amount: number
    opportunity_records: number
    quote_learning_records: number
  }
  items: Array<Record<string, unknown>>
  reason_clusters: Array<Record<string, unknown>>
  partner_rollup: Array<Record<string, unknown>>
  product_rollup: Array<Record<string, unknown>>
  decision_factor_rows: Array<Record<string, unknown>>
  competitor_signals: string[]
  management_questions: Record<string, unknown>
  next_action: string
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchWinLossIntelligenceDashboard(limit = 80) {
  const { data } = await http.get<WinLossIntelligenceDashboard>('/dashboard/win-loss-intelligence', {
    params: { limit },
  })
  return data
}

export interface WinLossFactorDetail extends Record<string, unknown> {
  factor: string
  summary: Record<string, number | string | null>
  items: Array<Record<string, unknown>>
  reason_clusters: Array<Record<string, unknown>>
  partner_rollup: Array<Record<string, unknown>>
  product_rollup: Array<Record<string, unknown>>
  competitor_signals: string[]
  reusable_lessons: string[]
  next_quote_guidance: string[]
  management_questions: Record<string, unknown>
  next_action: string
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchWinLossFactorDetail(factor: string, limit = 50) {
  const { data } = await http.get<WinLossFactorDetail>('/dashboard/win-loss-intelligence/factor-detail', {
    params: { factor, limit },
  })
  return data
}

export interface CustomerValueIntelligence {
  items: Array<Record<string, unknown>>
  summary: {
    total_accounts: number
    strategic_accounts: number
    growth_accounts: number
    active_prospects: number
    weighted_pipeline_amount: number
    won_order_amount: number
    open_quote_amount: number
    healthy_revenue_proxy: number
    commercial_quality_leader_count: number
    service_burden_account_count: number
  }
  commercial_quality_leaders: Array<Record<string, unknown>>
  service_burden_accounts: Array<Record<string, unknown>>
  management_questions: {
    who_to_follow: Array<unknown>
    why_follow: Array<unknown>
    what_is_commercially_healthy: Array<Record<string, unknown>>
    which_value_is_at_risk: Array<Record<string, unknown>>
    future_revenue_from: Array<Record<string, unknown>>
  }
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchCustomerValueIntelligence(limit = 50) {
  const { data } = await http.get<CustomerValueIntelligence>('/dashboard/customer-value-intelligence', {
    params: { limit },
  })
  return data
}

export interface CustomerValueDetail extends Record<string, unknown> {
  company_id: string
  customer_name: string
  summary: Record<string, number | string | boolean | null>
  commercial_quality: Record<string, unknown>
  project_scale: string
  strategic_value: string
  referral_value: string
  future_revenue_signal: string
  partner_focus: string[]
  product_focus: string[]
  customer_decision_factors: string[]
  active_risks: string[]
  quote_evidence: Array<Record<string, unknown>>
  order_evidence: Array<Record<string, unknown>>
  opportunity_evidence: Array<Record<string, unknown>>
  feedback_evidence: Array<Record<string, unknown>>
  win_loss_learning: Record<string, unknown>
  related_account: Record<string, unknown>
  management_questions: Record<string, unknown>
  source_paths: string[]
  next_action: string
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchCustomerValueDetail(companyId: string) {
  const { data } = await http.get<CustomerValueDetail>('/dashboard/customer-value-intelligence/detail', {
    params: { company_id: companyId },
  })
  return data
}

export interface RevenueForecastIntelligence {
  summary: {
    total_forecast_amount: number
    total_weighted_amount: number
    weighted_opportunity_amount: number
    open_quote_amount: number
    weighted_quote_amount: number
    booked_backlog_amount: number
    at_risk_weighted_amount: number
    item_count: number
    high_probability_count: number
    high_risk_count: number
    committed_backlog_amount: number
    forecastable_weighted_amount: number
    manual_follow_up_weighted_amount: number
    weak_signal_weighted_amount: number
    forecast_quality_score: number
  }
  total_weighted_amount: number
  open_quote_amount: number
  weighted_quote_amount: number
  at_risk_weighted_amount: number
  forecast_items: Array<Record<string, unknown>>
  high_probability_projects: Array<Record<string, unknown>>
  high_risk_projects: Array<Record<string, unknown>>
  committed_backlog: Array<Record<string, unknown>>
  forecastable_revenue: Array<Record<string, unknown>>
  manual_follow_up_revenue: Array<Record<string, unknown>>
  weak_signal_revenue: Array<Record<string, unknown>>
  revenue_bucket_mix: Array<Record<string, unknown>>
  source_type_mix: Array<Record<string, unknown>>
  forecast_by_partner: Array<Record<string, unknown>>
  forecast_by_product: Array<Record<string, unknown>>
  forecast_by_customer: Array<Record<string, unknown>>
  future_revenue_sources: string[]
  management_questions: Record<string, unknown>
  next_action: string
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchRevenueForecastIntelligence(limit = 80) {
  const { data } = await http.get<RevenueForecastIntelligence>('/dashboard/revenue-forecast-intelligence', {
    params: { limit },
  })
  return data
}

export interface RevenueForecastDetail extends Record<string, unknown> {
  forecast_key: string
  source_type: string
  source_id: string
  name: string
  customer_name: string
  partner_focus: string | null
  product_focus: string[]
  summary: Record<string, number | string | boolean | null>
  forecast_quality: Record<string, unknown>
  risk_reason: string | null
  opportunity_evidence: Record<string, unknown> | null
  quote_evidence: Record<string, unknown> | null
  order_evidence: Record<string, unknown> | null
  related_account: Record<string, unknown>
  source_paths: string[]
  management_questions: Record<string, unknown>
  next_action: string
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchRevenueForecastDetail(sourceType: string, sourceId: string) {
  const { data } = await http.get<RevenueForecastDetail>('/dashboard/revenue-forecast-intelligence/detail', {
    params: { source_type: sourceType, source_id: sourceId },
  })
  return data
}

export interface PartnerPerformanceIntelligence {
  summary: {
    partner_count: number
    active_partner_count: number
    quote_support_amount: number
    order_amount: number
    risk_partner_count: number
    p1_partner_count: number
    feedback_issue_count: number
    quote_allocation_candidate_count: number
    pilot_candidate_count: number
    allocation_risk_count: number
  }
  items: Array<Record<string, unknown>>
  top_investment_candidates: Array<Record<string, unknown>>
  quote_allocation_candidates: Array<Record<string, unknown>>
  pilot_candidates: Array<Record<string, unknown>>
  allocation_risks: Array<Record<string, unknown>>
  product_line_allocation: Array<Record<string, unknown>>
  delivery_or_feedback_risks: Array<Record<string, unknown>>
  partner_scoreboard: Array<Record<string, unknown>>
  management_questions: Record<string, unknown>
  next_action: string
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchPartnerPerformanceIntelligence(limit = 50) {
  const { data } = await http.get<PartnerPerformanceIntelligence>('/dashboard/partner-performance-intelligence', {
    params: { limit },
  })
  return data
}

export interface PartnerPerformanceDetail extends Record<string, unknown> {
  partner_id: string
  partner_name: string
  summary: Record<string, number | string | boolean | null>
  product_focus: string[]
  product_line_contribution: Array<Record<string, unknown>>
  allocation_profile: Record<string, unknown>
  cooperation_history: Record<string, unknown>
  quote_samples: Array<Record<string, unknown>>
  order_samples: Array<Record<string, unknown>>
  feedback_samples: Array<Record<string, unknown>>
  source_paths: string[]
  risk_signals: string[]
  missing_inputs: string[]
  management_questions: Record<string, unknown>
  next_action: string
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchPartnerPerformanceDetail(partner: string, limit = 50) {
  const { data } = await http.get<PartnerPerformanceDetail>('/dashboard/partner-performance-intelligence/detail', {
    params: { partner, limit },
  })
  return data
}

export interface ProductMarketFitIntelligence {
  summary: {
    product_line_count: number
    p1_product_line_count: number
    order_validated_count: number
    pilot_risk_count: number
    quote_learning_count: number
    feedback_signal_count: number
    order_amount: number
  }
  items: Array<Record<string, unknown>>
  top_product_lines: Array<Record<string, unknown>>
  pilot_risk_product_lines: Array<Record<string, unknown>>
  validated_buying_factors: Array<Record<string, unknown>>
  management_questions: Record<string, unknown>
  next_action: string
  safety: Record<string, boolean>
}

export async function fetchProductMarketFitIntelligence(limit = 50) {
  const { data } = await http.get<ProductMarketFitIntelligence>('/dashboard/product-market-fit-intelligence', {
    params: { limit },
  })
  return data
}

export interface ProductMarketFitFactorDetail extends Record<string, unknown> {
  factor: string
  summary: Record<string, number | string | null>
  items: Array<Record<string, unknown>>
  buying_factor_evidence: Array<Record<string, unknown>>
  partner_rollup: Array<Record<string, unknown>>
  product_rollup: Array<Record<string, unknown>>
  customer_objections: string[]
  competitor_signals: string[]
  project_experience: string[]
  source_paths: string[]
  customer_safe_candidates: string[]
  internal_only_boundaries: string[]
  management_questions: Record<string, unknown>
  next_action: string
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchProductMarketFitFactorDetail(factor: string, limit = 50) {
  const { data } = await http.get<ProductMarketFitFactorDetail>('/dashboard/product-market-fit-intelligence/factor-detail', {
    params: { factor, limit },
  })
  return data
}

export interface Account360Intelligence {
  summary: {
    account_count: number
    p1_account_count: number
    strategic_account_count: number
    open_opportunity_count: number
    open_quote_count: number
    open_feedback_count: number
    weighted_pipeline_amount: number
    won_order_amount: number
    full_relationship_count: number
    quote_to_order_learning_count: number
    repeat_or_referral_motion_count: number
    reactivation_motion_count: number
  }
  items: Array<Record<string, unknown>>
  recommended_accounts: Array<Record<string, unknown>>
  accounts_with_open_feedback: Array<Record<string, unknown>>
  repeat_business_candidates: Array<Record<string, unknown>>
  full_relationship_accounts: Array<Record<string, unknown>>
  quote_to_order_learning_accounts: Array<Record<string, unknown>>
  repeat_or_referral_accounts: Array<Record<string, unknown>>
  reactivation_accounts: Array<Record<string, unknown>>
  management_questions: Record<string, unknown>
  next_action: string
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchAccount360Intelligence(limit = 50) {
  const { data } = await http.get<Account360Intelligence>('/dashboard/account-360-intelligence', {
    params: { limit },
  })
  return data
}

export interface Account360Detail extends Record<string, unknown> {
  account_key: string
  customer_name: string
  current_stage: string
  priority: string
  partner_focus: string[]
  product_focus: string[]
  source_counts: Record<string, number>
  commercial_value: Record<string, number | string>
  detail_summary: Record<string, unknown>
  commercial_questions: Record<string, unknown>
  commercial_asset_coverage: Record<string, boolean>
  object_timeline: Array<Record<string, unknown>>
  next_commercial_motion: Record<string, unknown>
  customer_safe_boundary: string
  safety: Record<string, boolean>
}

export async function fetchAccount360Detail(accountKey: string) {
  const { data } = await http.get<Account360Detail>(
    `/dashboard/account-360-intelligence/${encodeURIComponent(accountKey)}`,
  )
  return data
}
