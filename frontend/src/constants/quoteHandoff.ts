/** D5.18 — soft quote handoff constants */

import {
  PRODUCT_FOCUS_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  quoteReadinessTagType,
} from '@/constants/productFit'

export {
  PRODUCT_FOCUS_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  quoteReadinessTagType,
}

export const QUOTE_HANDOFF_SAFETY =
  'This is an internal preparation aid only. It does not create quotes, generate pricing, promise inventory, confirm certifications, or send messages.'

export const HANDOFF_STATUS_LABELS: Record<string, string> = {
  ready_for_manual_quote_prep: 'Ready for manual quote prep',
  needs_customer_clarification: 'Needs customer clarification',
  not_ready: 'Not ready',
}

export const HANDOFF_PRIORITY_LABELS: Record<string, string> = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
}

export const PARTNER_ROUTE_LABELS: Record<string, string> = {
  hosun_lifting_systems: 'HOSUN lifting systems',
  jooboo_education_furniture: 'JOOBOO education furniture',
  project_supply: 'Project supply',
  medical_workspace: 'Medical / lab workspace',
  oem_odm_components: 'OEM / ODM components',
}

export const PRODUCT_SCOPE_LABELS: Record<string, string> = {
  adjustable_desk_frames: 'Adjustable desk frames',
  desk_legs: 'Desk legs',
  lifting_columns: 'Lifting columns',
  heavy_duty_lifting_systems: 'Heavy-duty lifting systems',
}

export function handoffStatusTagType(status: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  if (status === 'ready_for_manual_quote_prep') return 'success'
  if (status === 'needs_customer_clarification') return 'warning'
  return 'info'
}

export function handoffPriorityTagType(priority: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  if (priority === 'high') return 'danger'
  if (priority === 'medium') return 'warning'
  return 'info'
}

export type QuoteHandoffBrief = {
  lead_id: string
  company_name: string
  handoff_status: string
  handoff_priority: string
  quote_readiness: string
  sample_readiness: string
  opportunity_score: number
  recommended_partner_route: string[]
  recommended_product_scope: string[]
  known_context: string[]
  missing_customer_info: string[]
  supplier_preparation_notes: string[]
  customer_clarification_questions: string[]
  recommended_next_step: string
  quote_handoff_brief_text: string
  supplier_notes_text: string
  customer_questions_text: string
  warnings: string[]
  safety: {
    quote_created: boolean
    pricing_generated: boolean
    inventory_promised: boolean
    certification_promised: boolean
    lead_time_promised: boolean
    automatic_sending_enabled: boolean
  }
}
