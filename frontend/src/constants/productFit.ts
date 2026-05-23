/** D5.12 — product fit labels and helpers */

export const PRODUCT_FIT_SAFETY =
  'This card suggests product fit and project questions only. It does not create quotes, promise pricing, confirm inventory, or send messages.'

export const PRODUCT_FOCUS_LABELS: Record<string, string> = {
  hosun_lifting_systems: 'HOSUN Lifting Systems',
  adjustable_desk_frames: 'Adjustable Desk Frames',
  lifting_columns: 'Lifting Columns',
  jooboo_education_furniture: 'JOOBOO Education Furniture',
  medical_workspace: 'Medical Workspace',
  project_supply: 'Project Supply',
  oem_odm_components: 'OEM / ODM Components',
}

export const OPPORTUNITY_LEVEL_LABELS: Record<string, string> = {
  high_opportunity: 'High Opportunity',
  promising: 'Promising',
  needs_qualification: 'Needs Qualification',
  low_incomplete: 'Low / Incomplete',
}

export const PROJECT_TYPE_LABELS: Record<string, string> = {
  dealer_supply: 'Dealer Supply',
  project_based: 'Project-Based',
  education_project: 'Education Project',
  medical_workspace: 'Medical Workspace',
  oem_odm: 'OEM / ODM',
  general_office: 'General Office',
  unknown: 'Unknown',
}

export const QUOTE_READINESS_LABELS: Record<string, string> = {
  ready: 'Ready',
  almost_ready: 'Almost Ready',
  not_ready: 'Not Ready',
}

export const SAMPLE_READINESS_LABELS: Record<string, string> = {
  ready: 'Ready',
  needs_specs: 'Needs Specs',
  not_ready: 'Not Ready',
}

export const MISSING_QUOTE_INFO_LABELS: Record<string, string> = {
  contact_email_or_linkedin: 'Contact email or LinkedIn',
  product_type: 'Product type',
  quantity_or_volume: 'Quantity or volume',
  'desktop/frame size': 'Desktop / frame size',
  load_capacity_requirement: 'Load capacity requirement',
  color_or_finish: 'Color or finish',
  project_timeline: 'Project timeline',
  delivery_location: 'Delivery location',
  certification_requirement: 'Certification requirement',
  sample_quantity: 'Sample quantity',
  target_price_or_budget: 'Target price or budget',
  decision_maker_role: 'Decision maker role',
}

export function opportunityLevelTagType(level: string): 'success' | 'warning' | 'info' | 'danger' {
  if (level === 'high_opportunity') return 'success'
  if (level === 'promising') return 'warning'
  if (level === 'needs_qualification') return 'info'
  return 'danger'
}

export function quoteReadinessTagType(status: string): 'success' | 'warning' | 'danger' {
  if (status === 'ready') return 'success'
  if (status === 'almost_ready') return 'warning'
  return 'danger'
}

export function buildProductBrief(data: {
  company_name: string
  opportunity_level: string
  project_opportunity_score: number
  recommended_product_focus: string[]
  quote_readiness: string
  missing_quote_info: string[]
  recommended_next_product_action: string
}): string {
  const focus = data.recommended_product_focus
    .slice(0, 3)
    .map((f) => PRODUCT_FOCUS_LABELS[f] || f)
    .join(', ')
  const missing = data.missing_quote_info
    .slice(0, 4)
    .map((m) => MISSING_QUOTE_INFO_LABELS[m] || m)
    .join(', ')
  return [
    `Product Fit Brief — ${data.company_name}`,
    `Opportunity: ${OPPORTUNITY_LEVEL_LABELS[data.opportunity_level] || data.opportunity_level} (${data.project_opportunity_score})`,
    `Product focus: ${focus || '—'}`,
    `Quote readiness: ${QUOTE_READINESS_LABELS[data.quote_readiness] || data.quote_readiness}`,
    missing ? `Missing info: ${missing}` : 'Missing info: —',
    `Suggested next step: ${data.recommended_next_product_action}`,
  ].join('\n')
}
