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
