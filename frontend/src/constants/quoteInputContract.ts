/** D5.19 — quote input contract constants */

import {
  HANDOFF_STATUS_LABELS,
  PARTNER_ROUTE_LABELS,
  PRODUCT_SCOPE_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
} from '@/constants/quoteHandoff'

export {
  HANDOFF_STATUS_LABELS,
  PARTNER_ROUTE_LABELS,
  PRODUCT_SCOPE_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
}

export const QUOTE_INPUT_CONTRACT_SAFETY =
  'This contract prepares a future quote draft only. It does not create quotes, generate pricing, promise inventory, confirm certifications, or commit to lead times.'

export const QUOTE_MODULE_READINESS_LABELS: Record<string, string> = {
  ready_for_phase2_quote_draft: 'Ready for Phase 2 quote draft',
  needs_more_customer_info: 'Needs more customer information',
  not_quote_ready: 'Not quote ready',
}

export const KNOWN_REQUIREMENT_LABELS: Record<string, string> = {
  quantity_or_volume: 'Quantity or volume',
  product_type: 'Product type',
  frame_size_or_desktop_size: 'Frame / desktop size',
  load_capacity_requirement: 'Load capacity',
  color_or_finish: 'Color or finish',
  delivery_location: 'Delivery location',
  project_timeline: 'Project timeline',
  certification_requirement: 'Certification requirement',
  sample_quantity: 'Sample quantity',
  oem_customization_requirement: 'OEM customization',
  component_category: 'Component category',
}

export const KNOWN_REQUIREMENT_KEYS = Object.keys(KNOWN_REQUIREMENT_LABELS)

export function quoteModuleReadinessTagType(status: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  if (status === 'ready_for_phase2_quote_draft') return 'success'
  if (status === 'needs_more_customer_info') return 'warning'
  if (status === 'not_quote_ready') return 'info'
  return ''
}

export interface QuoteInputKnownRequirements {
  quantity_or_volume: string | null
  product_type: string | null
  frame_size_or_desktop_size: string | null
  load_capacity_requirement: string | null
  color_or_finish: string | null
  delivery_location: string | null
  project_timeline: string | null
  certification_requirement: string | null
  sample_quantity: string | null
  oem_customization_requirement: string | null
  component_category: string | null
}

export interface QuoteInputContract {
  lead_id: string
  company_name: string
  handoff_status: string
  quote_module_readiness: string
  recommended_partner_route: string[]
  recommended_product_scope: string[]
  quote_input_fields: {
    customer: {
      company_name: string
      contact_name: string | null
      contact_method_available: boolean
    }
    product_intent: {
      product_focus: string[]
      project_type: string
      sample_readiness: string
      quote_readiness: string
    }
    known_requirements: QuoteInputKnownRequirements
    missing_requirements: string[]
    recommended_questions: string[]
    supplier_preparation_notes: string[]
  }
  copyable_json: string
  copyable_handoff_summary: string
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
