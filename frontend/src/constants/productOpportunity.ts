/** D5.13 — product opportunity board constants */

import {
  MISSING_QUOTE_INFO_LABELS,
  OPPORTUNITY_LEVEL_LABELS,
  PRODUCT_FOCUS_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  opportunityLevelTagType,
  quoteReadinessTagType,
} from '@/constants/productFit'

export {
  PRODUCT_FOCUS_LABELS,
  OPPORTUNITY_LEVEL_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  opportunityLevelTagType,
  quoteReadinessTagType,
}

export const PRODUCT_OPPORTUNITY_SAFETY =
  'Product opportunity insights are advisory only. intelliOffice does not create quotes or promise pricing, inventory, certifications, or lead times.'

export type ProductOpportunityFilterKey =
  | 'all'
  | 'high_opportunity'
  | 'promising'
  | 'quote_ready'
  | 'almost_quote_ready'
  | 'sample_ready'
  | 'needs_specs'
  | 'lifting_system_fit'
  | 'project_supply'
  | 'education'
  | 'medical'
  | 'oem_odm'
  | 'missing_quantity'
  | 'missing_timeline'
  | 'missing_contact'

export const PRODUCT_OPPORTUNITY_FILTER_OPTIONS: { key: ProductOpportunityFilterKey; label: string }[] =
  [
    { key: 'all', label: 'All' },
    { key: 'high_opportunity', label: 'High Opportunity' },
    { key: 'promising', label: 'Promising' },
    { key: 'quote_ready', label: 'Quote Ready' },
    { key: 'almost_quote_ready', label: 'Almost Quote Ready' },
    { key: 'sample_ready', label: 'Sample Ready' },
    { key: 'needs_specs', label: 'Needs Specs' },
    { key: 'lifting_system_fit', label: 'Lifting Systems' },
    { key: 'project_supply', label: 'Project Supply' },
    { key: 'education', label: 'Education' },
    { key: 'medical', label: 'Medical' },
    { key: 'oem_odm', label: 'OEM / ODM' },
    { key: 'missing_quantity', label: 'Missing Quantity' },
    { key: 'missing_timeline', label: 'Missing Timeline' },
    { key: 'missing_contact', label: 'Missing Contact' },
  ]

export const DASHBOARD_OPPORTUNITY_CARDS: {
  key: ProductOpportunityFilterKey
  label: string
  summaryKey: keyof ProductOpportunitySummaryKeys
  tone?: 'primary' | 'success' | 'warning' | 'info' | 'danger'
}[] = [
  { key: 'high_opportunity', label: 'High Opportunity', summaryKey: 'high_opportunity', tone: 'success' },
  { key: 'quote_ready', label: 'Quote Ready', summaryKey: 'quote_ready', tone: 'primary' },
  { key: 'almost_quote_ready', label: 'Almost Quote Ready', summaryKey: 'almost_quote_ready', tone: 'warning' },
  { key: 'sample_ready', label: 'Sample Ready', summaryKey: 'sample_ready', tone: 'info' },
  { key: 'needs_specs', label: 'Needs Specs', summaryKey: 'needs_specs', tone: 'warning' },
  { key: 'lifting_system_fit', label: 'Lifting System Fit', summaryKey: 'lifting_system_fit', tone: 'primary' },
  { key: 'project_supply', label: 'Project Supply Fit', summaryKey: 'project_supply_fit', tone: 'info' },
  { key: 'oem_odm', label: 'OEM / ODM Potential', summaryKey: 'oem_odm_fit', tone: 'success' },
]

export type ProductOpportunitySummaryKeys = {
  total: number
  high_opportunity: number
  promising: number
  quote_ready: number
  almost_quote_ready: number
  sample_ready: number
  needs_specs: number
  lifting_system_fit: number
  project_supply_fit: number
  education_fit: number
  medical_fit: number
  oem_odm_fit: number
}

export const COMMON_QUOTE_QUESTIONS = `Common quote-readiness questions:
1. What quantity or volume should we consider?
2. What is the expected project timeline?
3. Which product type is most relevant: adjustable desk frames, lifting columns, desk legs, or education furniture?
4. Are there load capacity, size, color, finish, or certification requirements?
5. What delivery location should be used for quotation planning?`

export type ProductOpportunityBoardRow = {
  leadId: string
  companyName: string
  opportunityScore: number
  opportunityLevel: string
  projectType: string
  quoteReadiness: string
  sampleReadiness: string
  productFocus: string[]
  missingQuoteInfo: string[]
  nextProductAction: string
  nextAction: string | null
  followUpDate: string | null
  dueStatus: string | null
}

export function mapBoardRow(raw: {
  lead_id: string
  company_name: string
  opportunity_score?: number
  project_opportunity_score: number
  opportunity_level: string
  project_type: string
  quote_readiness: string
  sample_readiness: string
  recommended_product_focus?: string[]
  missing_quote_info?: string[]
  recommended_next_product_action?: string | null
  next_action?: string | null
  follow_up_date?: string | null
  due_status?: string | null
}): ProductOpportunityBoardRow {
  return {
    leadId: raw.lead_id,
    companyName: raw.company_name,
    opportunityScore: raw.opportunity_score ?? raw.project_opportunity_score,
    opportunityLevel: raw.opportunity_level,
    projectType: raw.project_type,
    quoteReadiness: raw.quote_readiness,
    sampleReadiness: raw.sample_readiness,
    productFocus: raw.recommended_product_focus ?? [],
    missingQuoteInfo: raw.missing_quote_info ?? [],
    nextProductAction: raw.recommended_next_product_action ?? '—',
    nextAction: raw.next_action ?? null,
    followUpDate: raw.follow_up_date ?? null,
    dueStatus: raw.due_status ?? null,
  }
}

export function quoteReadinessAdvice(quoteReadiness: string, sampleReadiness: string): string {
  if (quoteReadiness === 'ready') {
    return 'Prepare quote manually after confirming latest specs. Review quantity, dimensions, delivery location, and certification needs.'
  }
  if (quoteReadiness === 'almost_ready') {
    return 'Ask for missing quote information before preparing quote. Use discovery questions below.'
  }
  if (sampleReadiness === 'ready') {
    return 'Discuss sample request and target use case.'
  }
  if (sampleReadiness === 'needs_specs') {
    return 'Ask for product size, load capacity, finish, and quantity before sample discussion.'
  }
  return 'Complete contact research and confirm product interest before quote discussion.'
}

export function filterProductOpportunityRows(
  rows: ProductOpportunityBoardRow[],
  filter: ProductOpportunityFilterKey,
): ProductOpportunityBoardRow[] {
  if (filter === 'all') return rows
  return rows.filter((row) => {
    switch (filter) {
      case 'high_opportunity':
        return row.opportunityLevel === 'high_opportunity'
      case 'promising':
        return row.opportunityLevel === 'promising'
      case 'quote_ready':
        return row.quoteReadiness === 'ready'
      case 'almost_quote_ready':
        return row.quoteReadiness === 'almost_ready'
      case 'sample_ready':
        return row.sampleReadiness === 'ready'
      case 'needs_specs':
        return row.sampleReadiness === 'needs_specs'
      case 'lifting_system_fit':
        return row.productFocus.includes('hosun_lifting_systems')
      case 'project_supply':
        return row.productFocus.includes('project_supply')
      case 'education':
        return row.productFocus.includes('jooboo_education_furniture')
      case 'medical':
        return row.productFocus.includes('medical_workspace')
      case 'oem_odm':
        return row.productFocus.includes('oem_odm_components')
      case 'missing_quantity':
        return row.missingQuoteInfo.includes('quantity_or_volume')
      case 'missing_timeline':
        return row.missingQuoteInfo.includes('project_timeline')
      case 'missing_contact':
        return row.missingQuoteInfo.includes('contact_email_or_linkedin')
      default:
        return true
    }
  })
}

export function productFilterQueryPath(filter: ProductOpportunityFilterKey): string {
  return `/lead-intelligence?productFilter=${filter}`
}
