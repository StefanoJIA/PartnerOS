/** D5.14 — pre-quote prep constants */

import {
  MISSING_QUOTE_INFO_LABELS,
  PRODUCT_FOCUS_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  quoteReadinessTagType,
} from '@/constants/productFit'

export {
  PRODUCT_FOCUS_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  quoteReadinessTagType,
}

export const PRE_QUOTE_PREP_SAFETY =
  'This is preparation support only. It does not create quotes, generate pricing, promise inventory, confirm certifications, or send messages.'

export type PreQuoteBrief = {
  lead_id: string
  company_name: string
  quote_readiness: string
  sample_readiness: string
  recommended_product_focus: string[]
  project_type: string
  opportunity_score: number
  missing_quote_info: string[]
  quote_preparation_checklist: string[]
  sample_preparation_checklist: string[]
  recommended_customer_questions: string[]
  recommended_internal_next_steps: string[]
  recommended_next_action: string
  pre_quote_brief_text: string
  sample_discussion_brief_text: string
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
