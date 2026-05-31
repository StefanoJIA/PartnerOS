/** D5.4 — derived lead completeness (frontend, mirrors backend lead_completeness.py). */

import { NO_NEXT_ACTION } from '@/constants/followUpRhythm'

export type CompletenessStatus =
  | 'complete'
  | 'ready_for_outreach'
  | 'needs_contact_research'
  | 'incomplete'

export type CompletenessFilterKey =
  | 'all'
  | CompletenessStatus
  | 'missing_website'
  | 'missing_email_linkedin'
  | 'missing_next_action'
  | 'missing_enrichment'

export const COMPLETENESS_STATUS_LABELS: Record<CompletenessStatus, string> = {
  complete: 'Complete',
  ready_for_outreach: 'Ready for Outreach',
  needs_contact_research: 'Needs Contact Research',
  incomplete: 'Incomplete',
}

export const COMPLETENESS_FILTER_OPTIONS: { key: CompletenessFilterKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'complete', label: 'Complete' },
  { key: 'ready_for_outreach', label: 'Ready for Outreach' },
  { key: 'needs_contact_research', label: 'Needs Contact Research' },
  { key: 'incomplete', label: 'Incomplete' },
  { key: 'missing_website', label: 'Missing Website' },
  { key: 'missing_email_linkedin', label: 'Missing Email / LinkedIn' },
  { key: 'missing_next_action', label: 'Missing Next Action' },
  { key: 'missing_enrichment', label: 'Missing Enrichment' },
]

export const MISSING_FIELD_LABELS: Record<string, string> = {
  website: 'website',
  contact_name: 'contact_name',
  contact_email_or_linkedin: 'email / LinkedIn',
  contact_title: 'contact_title',
  next_action: 'next_action',
  enrichment: 'enrichment',
  touchpoint: 'touchpoint',
}

export type CompletenessInput = {
  companyName: string
  companyType?: string | null
  industry?: string | null
  notes?: string | null
  businessDescription?: string | null
  website?: string | null
  contactName?: string | null
  contactTitle?: string | null
  contactEmail?: string | null
  contactLinkedinUrl?: string | null
  companyLinkedinUrl?: string | null
  contactPhone?: string | null
  segments: string[]
  intelligenceScore: number
  suggestedNextActions?: string[]
  nextAction?: string | null
  enrichmentStatus?: string
  touchCount: number
}

export type CompletenessResult = {
  score: number
  status: CompletenessStatus
  statusLabel: string
  missingFields: string[]
  recommendedResearchAction: string
}

function hasText(value: string | null | undefined): boolean {
  if (value == null) return false
  const s = value.trim()
  return Boolean(s) && s !== '—' && s !== '-'
}

function hasEnrichment(status: string | undefined): boolean {
  const s = (status || '').trim().toLowerCase()
  if (!s || s === '—' || s === 'no runs') return false
  return true
}

function hasContactMethod(input: CompletenessInput): boolean {
  return (
    hasText(input.contactEmail) ||
    hasText(input.contactLinkedinUrl) ||
    hasText(input.companyLinkedinUrl)
  )
}

function statusFromScore(score: number): CompletenessStatus {
  if (score >= 80) return 'complete'
  if (score >= 60) return 'ready_for_outreach'
  if (score >= 40) return 'needs_contact_research'
  return 'incomplete'
}

function recommendAction(missing: string[], status: CompletenessStatus): string {
  if (missing.includes('website')) return 'Add website before enrichment.'
  if (missing.includes('contact_name')) return 'Find decision maker contact.'
  if (missing.includes('contact_email_or_linkedin')) return 'Add email or LinkedIn URL.'
  if (missing.includes('contact_title')) return 'Add contact title.'
  if (missing.includes('enrichment')) return 'Run enrichment before outreach.'
  if (missing.includes('next_action')) return 'Set next action.'
  if (status === 'complete' || status === 'ready_for_outreach') {
    return 'Generate draft and send by manual review.'
  }
  if (missing.includes('touchpoint')) return 'Generate draft after contact is confirmed.'
  return 'Review lead profile and fill missing fields.'
}

export function computeLeadCompleteness(input: CompletenessInput): CompletenessResult {
  let score = 0
  const missing: string[] = []

  if (hasText(input.companyName)) score += 10
  if (
    hasText(input.companyType) ||
    hasText(input.industry) ||
    hasText(input.notes) ||
    hasText(input.businessDescription)
  ) {
    score += 10
  }
  if (hasText(input.website)) score += 10
  else missing.push('website')

  if (hasText(input.contactName)) score += 10
  else missing.push('contact_name')
  if (hasText(input.contactTitle)) score += 5
  else missing.push('contact_title')
  if (hasContactMethod(input)) score += 10
  else missing.push('contact_email_or_linkedin')
  if (hasText(input.contactPhone)) score += 5

  if (input.segments.length) score += 10
  if (input.intelligenceScore > 0) score += 5
  const na = (input.nextAction || '').trim()
  const hasRec = (input.suggestedNextActions || []).some((a) => hasText(a))
  if (hasRec || (hasText(na) && na !== NO_NEXT_ACTION)) score += 5

  if (hasText(na) && na !== NO_NEXT_ACTION) score += 5
  else missing.push('next_action')
  if (hasEnrichment(input.enrichmentStatus)) score += 5
  else missing.push('enrichment')
  if (input.touchCount > 0) score += 5
  else missing.push('touchpoint')
  const draftOk = hasContactMethod(input) && (input.segments.length > 0 || input.intelligenceScore > 0)
  if (draftOk) score += 5

  const status = statusFromScore(score)
  return {
    score,
    status,
    statusLabel: COMPLETENESS_STATUS_LABELS[status],
    missingFields: missing,
    recommendedResearchAction: recommendAction(missing, status),
  }
}

export type CompletenessRow = {
  leadId: string
  companyName: string
  score: number
  status: CompletenessStatus
  statusLabel: string
  missingFields: string[]
  recommendedResearchAction: string
  segments: string[]
  nextAction: string
  lastTouch: string
}

export function computeCompletenessSummary(rows: CompletenessRow[]) {
  return {
    total: rows.length,
    complete: rows.filter((r) => r.status === 'complete').length,
    readyForOutreach: rows.filter((r) => r.status === 'ready_for_outreach').length,
    needsContactResearch: rows.filter((r) => r.status === 'needs_contact_research').length,
    incomplete: rows.filter((r) => r.status === 'incomplete').length,
    missingWebsite: rows.filter((r) => r.missingFields.includes('website')).length,
    missingContactMethod: rows.filter((r) => r.missingFields.includes('contact_email_or_linkedin')).length,
  }
}

export function filterCompletenessRows(rows: CompletenessRow[], filter: CompletenessFilterKey): CompletenessRow[] {
  if (filter === 'all') return rows
  if (filter === 'missing_website') return rows.filter((r) => r.missingFields.includes('website'))
  if (filter === 'missing_email_linkedin') {
    return rows.filter((r) => r.missingFields.includes('contact_email_or_linkedin'))
  }
  if (filter === 'missing_next_action') return rows.filter((r) => r.missingFields.includes('next_action'))
  if (filter === 'missing_enrichment') return rows.filter((r) => r.missingFields.includes('enrichment'))
  return rows.filter((r) => r.status === filter)
}

export function completenessStatusTagType(status: CompletenessStatus) {
  if (status === 'complete') return 'success'
  if (status === 'ready_for_outreach') return 'primary'
  if (status === 'needs_contact_research') return 'warning'
  return 'danger'
}

export function applyContactResearchPreset(touch: {
  interaction_type: string
  channel: string
  subject?: string | null
  summary?: string | null
  next_action?: string | null
}) {
  touch.interaction_type = 'contact_research'
  touch.channel = 'manual_research'
  touch.subject = 'Contact research'
  touch.summary = 'Contact research needed / contact info updated'
  if (!touch.next_action?.trim()) {
    touch.next_action = 'Confirm decision maker and contact method before outreach'
  }
}
