/** Display labels for market_fit_segments (Lead Intelligence / pilot review). */

export const SEGMENT_LABELS: Record<string, string> = {
  lift_system_signal: 'Lifting System Signal',
  general_office_furniture_only: 'General Office Furniture',
  oem_odm_fit: 'OEM / ODM Signal',
  medical_vertical: 'Medical / Healthcare Vertical',
  education_vertical: 'Education Vertical',
  heavy_duty_fit: 'Heavy-Duty / Industrial',
  project_based_furniture: 'Project-Based Furniture',
}

export const SEGMENT_TOOLTIPS: Record<string, string> = {
  lift_system_signal:
    'Clear height-adjustable / lifting column / sit-stand signals — prioritize for HOSUN frame & column outreach.',
  general_office_furniture_only:
    'Office furniture related but no explicit lift-system cue yet. Maintain lightly or enrich before scoring up.',
  oem_odm_fit: 'OEM/ODM or private-label project signals — validate engineering & certification path.',
  medical_vertical: 'Healthcare, lab, or clinical workstation context.',
  education_vertical: 'Education furniture or campus learning environment.',
  heavy_duty_fit: 'Heavy-duty or industrial-grade lifting requirements.',
  project_based_furniture: 'Contract interiors, installation, or project-based furniture delivery.',
}

export type SegmentFilterKey =
  | 'all'
  | 'lift_system_signal'
  | 'medical_vertical'
  | 'education_vertical'
  | 'project_based_furniture'
  | 'general_office_furniture_only'

export const SEGMENT_FILTER_OPTIONS: { key: SegmentFilterKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'lift_system_signal', label: 'Lifting' },
  { key: 'medical_vertical', label: 'Medical' },
  { key: 'education_vertical', label: 'Education' },
  { key: 'project_based_furniture', label: 'Project' },
  { key: 'general_office_furniture_only', label: 'General Office' },
]

export function segmentLabel(slug: string): string {
  return SEGMENT_LABELS[slug] || slug
}

export function segmentTooltip(slug: string): string {
  return SEGMENT_TOOLTIPS[slug] || ''
}

export function segmentTagType(slug: string): 'primary' | 'success' | 'info' | 'warning' | 'danger' {
  if (slug === 'general_office_furniture_only') return 'info'
  if (slug === 'lift_system_signal') return 'success'
  if (slug === 'medical_vertical') return 'warning'
  if (slug === 'project_based_furniture') return 'primary'
  return 'primary'
}

export function priorityHint(score: number, priority: string | null | undefined): string {
  if (score >= 70) return 'High fit — follow up this week'
  if (score >= 50) return 'Moderate — enrich & qualify'
  if (priority === 'High' || priority === 'high') return 'Priority flagged — review'
  return 'Monitor — gather more signals'
}
