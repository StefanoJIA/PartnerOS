import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export type PartnerOnboardingStage =
  | 'discovery'
  | 'product_mapping'
  | 'quote_ready'
  | 'portal_ready'
  | 'demo_ready'
  | 'active_partner'
  | 'paused'

export interface PartnerOnboardingChecklistItem {
  key: string
  label: string
  done: boolean
  detail: string
}

export interface PartnerOnboardingLinks {
  partner_detail: string
  product_catalog: string
  demo_walkthrough: string
  market_response: string
  orders: string
}

export interface PartnerOnboardingRecord {
  partner_id: string
  partner_name: string
  partner_code: string | null
  partner_type: string | null
  product_focus: string[]
  target_markets: string[]
  onboarding_stage: PartnerOnboardingStage
  readiness_score: number
  readiness_summary: string
  missing_items: string[]
  next_action: string
  checklist: PartnerOnboardingChecklistItem[]
  links: PartnerOnboardingLinks
  is_reference_partner: boolean
  safety: Record<string, boolean>
}

export interface PartnerOnboardingResponse {
  status: string
  stage_order: string[]
  checklist_keys: string[]
  summary: {
    total_partners: number
    reference_partner_count: number
    demo_ready_count: number
    quote_ready_count: number
    portal_ready_count: number
    active_partner_count: number
    paused_count: number
    safety: Record<string, boolean>
  }
  items: PartnerOnboardingRecord[]
  future_partner_placeholder: PartnerOnboardingRecord | null
  safety: Record<string, boolean>
}

export async function fetchPartnerOnboarding() {
  const { data } = await http.get<V1Envelope<PartnerOnboardingResponse>>('/v1/partner-onboarding')
  return data.data
}

