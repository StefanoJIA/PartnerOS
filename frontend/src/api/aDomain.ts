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
