import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export interface GrowthCampaignMetrics {
  company_count: number
  lead_count: number
  contact_count: number
  quote_count: number
  quote_value: string
  order_count: number
  order_value: string
  feedback_ticket_count: number
  shipment_risk_count: number
  market_signal_count: number
}

export interface GrowthCampaign {
  id: string
  name: string
  partner_focus: string
  product_focus: string[]
  target_segment: string
  goal: string
  status: string
  next_action: string
  metrics: GrowthCampaignMetrics
  links: Record<string, string>
}

export interface GrowthSegment {
  segment_key: string
  segment_label: string
  company_count: number
  lead_count: number
  contact_count: number
  campaign_ids: string[]
  source: string
  recommended_use: string
}

export interface GrowthOutreachSequence {
  campaign_id: string
  lead_id: string | null
  company_id: string | null
  company_name: string
  contact_name: string | null
  lead_name: string | null
  channel: string
  drafts: {
    zh: { subject: string; body: string }
    en: { subject: string; body: string }
  }
  follow_up_task: {
    title: string
    next_action: string
    due_date: string
  }
  manual_event_options: Array<{ value: string; label: string }>
}

export interface GrowthAttribution {
  campaign_id: string
  quote_count: number
  order_count: number
  quote_value: string
  order_value: string
  quote_ids: string[]
  order_ids: string[]
  explanation_zh: string
}

export interface GrowthFeedbackLoop {
  campaign_id: string
  feedback_ticket_count: number
  shipment_risk_count: number
  market_signal_count: number
  recommendation_zh: string
}

export interface GrowthOperationsConsole {
  status: string
  positioning_zh: string
  competitor_alignment: {
    sales_yi_adapted: string[]
    constant_contact_adapted: string[]
    partneros_difference: string
  }
  campaigns: GrowthCampaign[]
  segments: GrowthSegment[]
  outreach_sequences: GrowthOutreachSequence[]
  attribution: GrowthAttribution[]
  feedback_loop: GrowthFeedbackLoop[]
  safety: {
    external_crm_connected: boolean
    constant_contact_connected: boolean
    email_sent: boolean
    sms_sent: boolean
    linkedin_sent: boolean
    customer_notified: boolean
    supplier_notified: boolean
    quote_status_changed: boolean
    order_status_changed: boolean
    staging_validated: boolean
    human_review_required: boolean
  }
}

export async function fetchGrowthOperationsConsole(): Promise<GrowthOperationsConsole> {
  const { data } = await http.get<V1Envelope<GrowthOperationsConsole>>('/v1/growth/operations-console')
  return data.data
}

export interface GrowthCampaignWorkspaceSummary {
  quote_count: number
  order_count: number
  feedback_ticket_count: number
  shipment_risk_count: number
  market_signal_count: number
  quote_value: string
  order_value: string
  quote_ids: string[]
  order_ids: string[]
  feedback_ticket_ids: string[]
  shipment_risk_ids: string[]
  market_signal_ids: string[]
  explanation_zh: string
}

export interface GrowthCampaignWorkspaceRow {
  id: string
  name: string
  partner_focus: string
  product_focus: string[]
  target_segment: string | null
  goal: string | null
  status: string
  status_label: string
  owner: string | null
  next_action: string | null
  notes: string | null
  created_at: string
  updated_at: string
  summary?: GrowthCampaignWorkspaceSummary
}

export interface GrowthCampaignTaskRow {
  id: string
  campaign_id: string
  company_id: string | null
  contact_id: string | null
  company_name: string | null
  contact_name: string | null
  task_type: string
  task_type_label: string
  language: string
  draft_subject: string | null
  draft_body: string | null
  status: string
  status_label: string
  due_date: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface GrowthCampaignWorkspaceList {
  campaigns: GrowthCampaignWorkspaceRow[]
  safety: Record<string, boolean>
}

export interface GrowthCampaignWorkspaceDetail {
  campaign: GrowthCampaignWorkspaceRow
  tasks: GrowthCampaignTaskRow[]
  opportunities: GrowthOpportunityRow[]
  summary: GrowthCampaignWorkspaceSummary
  manual_status_options: Array<{ value: string; label: string }>
  opportunity_stage_options: Array<{ value: string; label: string }>
  opportunity_status_options: Array<{ value: string; label: string }>
  safety: Record<string, boolean>
}

export interface GrowthCampaignCreatePayload {
  name: string
  partner_focus: string
  product_focus: string[]
  target_segment?: string | null
  goal?: string | null
  status?: string
  owner?: string | null
  next_action?: string | null
  notes?: string | null
}

export type GrowthCampaignUpdatePayload = Partial<GrowthCampaignCreatePayload>

export interface GrowthCampaignTaskCreatePayload {
  company_id?: string | null
  contact_id?: string | null
  task_type?: string
  language?: string
  draft_subject?: string | null
  draft_body?: string | null
  status?: string
  due_date?: string | null
  notes?: string | null
}

export type GrowthCampaignTaskUpdatePayload = Partial<GrowthCampaignTaskCreatePayload>

export interface GrowthOpportunityRecommendation {
  id: string
  source_type: 'market_response' | 'quote_learning' | string
  source_id: string
  priority: string
  suggested_probability: number
  suggested_decision_stage: string
  risk_signal: string
  recommended_next_action: string
  reason: string
  path: string
  manual_apply_required: boolean
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
  safety: Record<string, boolean>
}

export interface GrowthOpportunityStageGate {
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

export interface GrowthOpportunityExecutionContext {
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

export interface GrowthOpportunityRow {
  id: string
  opportunity_name: string
  company_id: string | null
  company_name: string | null
  lead_id: string | null
  campaign_id: string | null
  quote_id: string | null
  order_id: string | null
  partner_focus: string | null
  product_focus: string[]
  customer_segment: string | null
  project_size: string | null
  estimated_value: string | null
  decision_stage: string
  decision_stage_label: string
  competition: string | null
  risk: string | null
  probability: number
  priority: string
  owner: string | null
  next_action: string | null
  blocker: string | null
  status: string
  status_label: string
  expected_close_date: string | null
  outcome_status: string | null
  outcome_reason_category: string | null
  customer_decision_factors: string[]
  product_factors: string[]
  partner_factors: string[]
  outcome_recorded_at: string | null
  won_reason: string | null
  lost_reason: string | null
  notes: string | null
  path: string
  recommendations: GrowthOpportunityRecommendation[]
  partner_fit?: GrowthOpportunityRecommendation['partner_fit']
  stage_gate: GrowthOpportunityStageGate
  execution_context: GrowthOpportunityExecutionContext
  created_at: string
  updated_at: string
}

export interface GrowthOpportunityList {
  opportunities: GrowthOpportunityRow[]
  stage_options: Array<{ value: string; label: string }>
  status_options: Array<{ value: string; label: string }>
  safety: Record<string, boolean>
}

export interface GrowthOpportunityPayload {
  opportunity_name: string
  company_id?: string | null
  lead_id?: string | null
  campaign_id?: string | null
  quote_id?: string | null
  order_id?: string | null
  partner_focus?: string | null
  product_focus?: string[]
  customer_segment?: string | null
  project_size?: string | null
  estimated_value?: string | null
  decision_stage?: string
  competition?: string | null
  risk?: string | null
  probability?: number
  priority?: string
  owner?: string | null
  next_action?: string | null
  blocker?: string | null
  status?: string
  expected_close_date?: string | null
  won_reason?: string | null
  lost_reason?: string | null
  notes?: string | null
}

export type GrowthOpportunityUpdatePayload = Partial<GrowthOpportunityPayload>

export interface WinLossRecord {
  id: string
  source_type: string
  source_id: string
  outcome: string
  reason_category?: string | null
  customer: string | null
  opportunity_name: string | null
  quote_number?: string | null
  partner_focus: string | null
  product_focus: string[]
  commercial_value: string | null
  competitor_signal: string | null
  customer_decision_factors: string[]
  product_factors?: string[]
  partner_factors?: string[]
  won_reason: string | null
  lost_reason: string | null
  commercial_lesson: string
  next_action: string
  owner: string | null
  path: string
  created_at: string | null
  updated_at: string | null
  safety: Record<string, boolean>
}

export interface WinLossIntelligence {
  items: WinLossRecord[]
  summary: {
    total: number
    won: number
    lost: number
    win_rate: number | null
    opportunity_records: number
    quote_learning_records: number
  }
  filters: Record<string, string | null>
  safety: Record<string, boolean>
}

export interface OpportunityWinLossPayload {
  outcome: string
  reason_category?: string | null
  won_reason?: string | null
  lost_reason?: string | null
  competitor_signal?: string | null
  customer_decision_factors?: string[]
  product_dimensions?: string[]
  product_factors?: string[]
  partner_factors?: string[]
  partner_focus?: string | null
  product_focus?: string[] | null
  next_action?: string | null
  owner?: string | null
  notes?: string | null
}

export async function fetchGrowthCampaigns(): Promise<GrowthCampaignWorkspaceList> {
  const { data } = await http.get<V1Envelope<GrowthCampaignWorkspaceList>>('/v1/growth/campaigns')
  return data.data
}

export async function createGrowthCampaign(payload: GrowthCampaignCreatePayload): Promise<GrowthCampaignWorkspaceDetail> {
  const { data } = await http.post<V1Envelope<GrowthCampaignWorkspaceDetail>>('/v1/growth/campaigns', payload)
  return data.data
}

export async function fetchGrowthCampaignDetail(id: string): Promise<GrowthCampaignWorkspaceDetail> {
  const { data } = await http.get<V1Envelope<GrowthCampaignWorkspaceDetail>>(`/v1/growth/campaigns/${id}`)
  return data.data
}

export async function updateGrowthCampaign(
  id: string,
  payload: GrowthCampaignUpdatePayload,
): Promise<GrowthCampaignWorkspaceDetail> {
  const { data } = await http.patch<V1Envelope<GrowthCampaignWorkspaceDetail>>(`/v1/growth/campaigns/${id}`, payload)
  return data.data
}

export async function createGrowthCampaignTask(
  id: string,
  payload: GrowthCampaignTaskCreatePayload,
): Promise<GrowthCampaignWorkspaceDetail> {
  const { data } = await http.post<V1Envelope<GrowthCampaignWorkspaceDetail>>(`/v1/growth/campaigns/${id}/tasks`, payload)
  return data.data
}

export async function updateGrowthCampaignTask(
  id: string,
  payload: GrowthCampaignTaskUpdatePayload,
): Promise<GrowthCampaignWorkspaceDetail> {
  const { data } = await http.patch<V1Envelope<GrowthCampaignWorkspaceDetail>>(`/v1/growth/tasks/${id}`, payload)
  return data.data
}

export async function fetchGrowthOpportunities(): Promise<GrowthOpportunityList> {
  const { data } = await http.get<V1Envelope<GrowthOpportunityList>>('/v1/growth/opportunities')
  return data.data
}

export async function createGrowthOpportunity(payload: GrowthOpportunityPayload): Promise<GrowthOpportunityRow> {
  const { data } = await http.post<V1Envelope<GrowthOpportunityRow>>('/v1/growth/opportunities', payload)
  return data.data
}

export async function updateGrowthOpportunity(
  id: string,
  payload: GrowthOpportunityUpdatePayload,
): Promise<GrowthOpportunityRow> {
  const { data } = await http.patch<V1Envelope<GrowthOpportunityRow>>(`/v1/growth/opportunities/${id}`, payload)
  return data.data
}

export async function fetchWinLossIntelligence(params?: {
  outcome?: string
  partner_focus?: string
  product_focus?: string
}): Promise<WinLossIntelligence> {
  const { data } = await http.get<V1Envelope<WinLossIntelligence>>('/v1/growth/win-loss', { params })
  return data.data
}

export async function recordOpportunityWinLoss(
  id: string,
  payload: OpportunityWinLossPayload,
): Promise<WinLossRecord> {
  const { data } = await http.post<V1Envelope<WinLossRecord>>(`/v1/growth/opportunities/${id}/win-loss`, payload)
  return data.data
}
