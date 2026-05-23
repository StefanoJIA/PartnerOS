/** D5.15 — product-aware draft constants */

export const PRODUCT_AWARE_DRAFT_SAFETY =
  'This draft is advisory and human-reviewed. intelliOffice does not send messages, create quotes, promise pricing, confirm inventory, or verify certifications.'

export const DRAFT_CHANNEL_OPTIONS = [
  { value: 'email_intro', label: 'Email intro' },
  { value: 'email_followup', label: 'Email follow-up' },
  { value: 'linkedin_connect', label: 'LinkedIn connect' },
  { value: 'linkedin_followup', label: 'LinkedIn follow-up' },
] as const

export const DRAFT_PURPOSE_OPTIONS = [
  { value: 'product_discovery', label: 'Product discovery' },
  { value: 'quote_readiness', label: 'Quote readiness' },
  { value: 'sample_discussion', label: 'Sample discussion' },
  { value: 'project_discovery', label: 'Project discovery' },
  { value: 'oem_odm_discovery', label: 'OEM / ODM discovery' },
  { value: 'general_intro', label: 'General intro' },
  { value: 'follow_up_after_intro', label: 'Follow-up after intro' },
  { value: 'follow_up_after_sample', label: 'Follow-up after sample' },
] as const

export const DRAFT_TONE_OPTIONS = [
  { value: 'concise', label: 'Concise' },
  { value: 'warm', label: 'Warm' },
  { value: 'formal', label: 'Formal' },
] as const

export type ProductAwareDraft = {
  lead_id: string
  company_name: string
  channel: string
  draft_purpose: string
  tone: string
  language: string
  subject?: string | null
  body?: string | null
  linkedin_note?: string | null
  questions: string[]
  recommended_next_action: string
  suggested_follow_up_days: number
  source_context: {
    product_focus: string[]
    quote_readiness: string
    sample_readiness: string
    missing_quote_info: string[]
  }
  safety: {
    quote_created: boolean
    pricing_generated: boolean
    inventory_promised: boolean
    certification_promised: boolean
    lead_time_promised: boolean
    automatic_sending_enabled: boolean
  }
  warnings: string[]
}
