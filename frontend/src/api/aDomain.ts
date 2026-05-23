import { http } from '@/api/http'

export type LeadIntelligenceWorkflow = {
  lead: {
    id: string
    lead_name: string
    company_id: string
    current_stage: string
    lead_type: string
    source: string
    next_action?: string | null
    next_action_due_date?: string | null
    product_interest?: string | null
    priority?: string | null
  }
  company: {
    id: string
    company_name: string
    company_type?: string
    website?: string | null
    linkedin_url?: string | null
    product_interest_tags?: string | null
    business_description?: string | null
    strategic_level?: string | null
  }
  primary_contact: {
    id: string
    first_name: string
    last_name: string
    email?: string | null
    title?: string | null
    phone?: string | null
    linkedin_url?: string | null
  } | null
  intelligence_score: number
  score_breakdown: Record<string, number>
  suggested_next_actions: string[]
  market_intelligence_count: number
  market_intelligence_preview_ids: string[]
  market_fit_segments?: string[]
}

export async function fetchLeadIntelligenceWorkflow(leadId: string) {
  const { data } = await http.get<LeadIntelligenceWorkflow>(`/a-domain/leads/${leadId}/workflow`)
  return data
}

export type TouchpointBody = {
  interaction_type: string
  channel: string
  subject?: string | null
  content?: string | null
  summary?: string | null
  direction?: string | null
  next_action?: string | null
  next_action_due_date?: string | null
  interaction_next_action?: string | null
  interaction_next_action_due_date?: string | null
}

export async function postLeadIntelligenceTouchpoint(leadId: string, body: TouchpointBody) {
  const { data } = await http.post<{
    interaction_id: string
    lead_id: string
    next_action?: string | null
    next_action_due_date?: string | null
  }>(`/a-domain/leads/${leadId}/touchpoint`, body)
  return data
}

export type ContactResearchPayload = {
  company?: {
    website?: string
    company_type?: string
    notes?: string
  }
  contact?: {
    name?: string
    title?: string
    email?: string
    phone?: string
    linkedin_url?: string
  }
  lead?: {
    next_action?: string
  }
  touchpoint_note?: string
}

export type LeadCompletenessRow = {
  lead_id: string
  company_name: string
  lead_name: string
  score: number
  status: string
  status_label: string
  missing_fields: string[]
  recommended_research_action: string
  segment?: string | null
  segments: string[]
  next_action?: string | null
  last_touchpoint?: string | null
}

export type LeadCompletenessResponse = {
  rows: LeadCompletenessRow[]
  summary: {
    total: number
    complete: number
    ready_for_outreach: number
    needs_contact_research: number
    incomplete: number
    missing_website: number
    missing_contact_method: number
  }
}

export async function fetchLeadCompleteness() {
  const { data } = await http.get<LeadCompletenessResponse>('/a-domain/lead-completeness')
  return data
}

export async function postContactResearch(leadId: string, body: ContactResearchPayload) {
  const { data } = await http.post<{
    lead_id: string
    interaction_id: string
    completeness: LeadCompletenessRow
  }>(`/a-domain/leads/${leadId}/contact-research`, body)
  return data
}

export type LeadTimelineItem = {
  id: string
  timestamp: string | null
  type: string
  channel: string
  title: string
  summary?: string | null
  is_manual_send: boolean
  is_contact_research: boolean
}

export type LeadTimeline = {
  lead_id: string
  company_name: string
  next_action?: string | null
  next_follow_up_date?: string | null
  due_status?: string | null
  days_until_due?: number | null
  last_touchpoint_at?: string | null
  follow_up_hint: string
  items: LeadTimelineItem[]
  stats: {
    total_touchpoints: number
    manual_sent_count: number
    contact_research_count: number
    last_channel?: string | null
  }
}

export async function fetchLeadTimeline(leadId: string) {
  const { data } = await http.get<LeadTimeline>(`/a-domain/leads/${leadId}/timeline`)
  return data
}

export type FollowUpQueueRow = {
  lead_id: string
  company_name: string
  lead_score: number
  segments: string[]
  next_action?: string | null
  next_follow_up_date?: string | null
  due_status: string
  days_until_due?: number | null
  last_touchpoint_at?: string | null
  waiting_reply: boolean
  recommended_action: string
}

export type FollowUpQueueResponse = {
  summary: {
    total: number
    overdue: number
    due_today: number
    due_soon: number
    no_follow_up_date: number
    waiting_reply: number
  }
  rows: FollowUpQueueRow[]
}

export async function fetchFollowUpQueue() {
  const { data } = await http.get<FollowUpQueueResponse>('/a-domain/follow-up-queue')
  return data
}

export type FollowUpSchedulePayload = {
  next_follow_up_date?: string | null
  next_action?: string
  status_note?: string
  clear_date?: boolean
}

export async function patchLeadFollowUp(leadId: string, body: FollowUpSchedulePayload) {
  const { data } = await http.patch<{
    lead_id: string
    company_name: string
    next_action?: string | null
    next_follow_up_date?: string | null
    due_status: string
    days_until_due?: number | null
    interaction_id: string
  }>(`/a-domain/leads/${leadId}/follow-up`, body)
  return data
}

export type ProductFit = {
  lead_id: string
  company_name: string
  recommended_product_focus: string[]
  project_opportunity_score: number
  opportunity_level: string
  project_type: string
  quote_readiness: string
  sample_readiness: string
  missing_quote_info: string[]
  recommended_discovery_questions: string[]
  recommended_next_product_action: string
  sales_angle: string
  warnings: string[]
}

export async function fetchProductFit(leadId: string) {
  const { data } = await http.get<ProductFit>(`/a-domain/leads/${leadId}/product-fit`)
  return data
}

export type ProductOpportunityBoardRow = {
  lead_id: string
  company_name: string
  project_opportunity_score: number
  opportunity_level: string
  project_type: string
  quote_readiness: string
  sample_readiness: string
  recommended_product_focus: string[]
}

export async function fetchProductOpportunityBoard() {
  const { data } = await http.get<{
    summary: {
      total: number
      high_opportunity: number
      quote_ready: number
      almost_ready: number
      needs_specs: number
      oem_odm_potential: number
      lifting_system_fit: number
    }
    rows: ProductOpportunityBoardRow[]
  }>('/a-domain/product-opportunity-board')
  return data
}
