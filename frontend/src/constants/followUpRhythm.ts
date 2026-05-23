/** D5.2.7 — derived follow-up categories (frontend only, no DB). */

import { SEGMENT_FILTER_OPTIONS } from '@/constants/leadSegments'

export const NO_NEXT_ACTION = 'No next action set.'

export type FollowUpCategory =
  | 'needs_first_outreach'
  | 'waiting_for_reply'
  | 'follow_up_soon'
  | 'needs_contact_research'
  | 'high_priority'
  | 'needs_enrichment'
  | 'ready_for_catalog_quote'

export type OperationFilterKey =
  | 'today_focus'
  | 'needs_first_outreach'
  | 'waiting_for_reply'
  | 'follow_up_soon'
  | 'needs_contact_research'
  | 'high_priority'
  | 'needs_enrichment'
  | 'ready_for_catalog_quote'

export type RhythmLeadRow = {
  score: number
  segments: string[]
  nextAction: string
  touchCount: number
  lastTouch: string
  lastTouchDate: string | null
  contactEmail: string | null
  linkedinUrl: string | null
  enrichmentStatus: string
  companyWebsite: string | null
}

export const OPERATION_FILTER_OPTIONS: { key: OperationFilterKey; label: string }[] = [
  { key: 'today_focus', label: 'Today Focus' },
  { key: 'needs_first_outreach', label: 'Needs First Outreach' },
  { key: 'waiting_for_reply', label: 'Waiting for Reply' },
  { key: 'follow_up_soon', label: 'Follow Up Soon' },
  { key: 'needs_contact_research', label: 'Needs Contact Research' },
  { key: 'high_priority', label: 'High Priority' },
  { key: 'needs_enrichment', label: 'Needs Enrichment' },
  { key: 'ready_for_catalog_quote', label: 'Ready for Catalog / Quote' },
]

export const STATUS_BADGE_LABELS: Record<FollowUpCategory, string> = {
  needs_first_outreach: 'First outreach',
  waiting_for_reply: 'Waiting reply',
  follow_up_soon: 'Follow up soon',
  needs_contact_research: 'Research contact',
  high_priority: 'High priority',
  needs_enrichment: 'Needs enrichment',
  ready_for_catalog_quote: 'Catalog / quote',
}

const HIGH_PRIORITY_SEGMENTS = new Set([
  'lift_system_signal',
  'project_based_furniture',
  'medical_vertical',
])

const TODAY_FOCUS_CATEGORIES: FollowUpCategory[] = [
  'high_priority',
  'needs_first_outreach',
  'waiting_for_reply',
  'follow_up_soon',
]

function lower(text: string): string {
  return text.toLowerCase()
}

function matchesAny(text: string, phrases: string[]): boolean {
  const t = lower(text)
  return phrases.some((p) => t.includes(p))
}

export function isOlderThanDays(iso: string | null, days: number): boolean {
  if (!iso) return false
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return false
  return Date.now() - d.getTime() >= days * 24 * 60 * 60 * 1000
}

export function classifyFollowUpCategories(row: RhythmLeadRow): FollowUpCategory[] {
  const cats: FollowUpCategory[] = []
  const na = row.nextAction
  const lt = row.lastTouch
  const hasEmail = Boolean(row.contactEmail?.trim())
  const hasLinkedIn = Boolean(row.linkedinUrl?.trim())
  const hasSegments = row.segments.length > 0
  const enrichLower = lower(row.enrichmentStatus || '')
  const manuallySent =
    lower(lt).includes('manually_sent=true') || lower(lt).includes('manual outreach')

  if (row.touchCount === 0 && hasSegments) {
    cats.push('needs_first_outreach')
  }

  if (
    (manuallySent && matchesAny(na, ['wait', 'follow up', 'waiting'])) ||
    (row.touchCount > 0 && matchesAny(na, ['wait for reply', 'waiting for']))
  ) {
    cats.push('waiting_for_reply')
  }

  if (
    matchesAny(na, ['follow up', 'follow-up']) ||
    (row.touchCount > 0 && manuallySent && isOlderThanDays(row.lastTouchDate, 3))
  ) {
    cats.push('follow_up_soon')
  }

  if ((!hasEmail && !hasLinkedIn) || matchesAny(na, ['research contact'])) {
    cats.push('needs_contact_research')
  }

  if (
    row.score >= 70 ||
    row.segments.some((s) => HIGH_PRIORITY_SEGMENTS.has(s)) ||
    matchesAny(na, ['quotation', 'quote', 'sample', 'meeting'])
  ) {
    cats.push('high_priority')
  }

  const needsEnrich =
    row.enrichmentStatus === 'No runs' ||
    row.enrichmentStatus === '—' ||
    enrichLower.includes('no run') ||
    (Boolean(row.companyWebsite?.trim()) && !enrichLower.startsWith('completed'))
  if (needsEnrich && !enrichLower.startsWith('completed')) {
    cats.push('needs_enrichment')
  }

  if (matchesAny(na, ['catalog', 'quotation', 'quote', 'sample', 'meeting'])) {
    cats.push('ready_for_catalog_quote')
  }

  return cats
}

export function primaryStatusBadge(categories: FollowUpCategory[]): FollowUpCategory | null {
  const order: FollowUpCategory[] = [
    'high_priority',
    'needs_contact_research',
    'waiting_for_reply',
    'follow_up_soon',
    'needs_first_outreach',
    'ready_for_catalog_quote',
    'needs_enrichment',
  ]
  for (const c of order) {
    if (categories.includes(c)) return c
  }
  return null
}

export type DailySummaryCounts = {
  total: number
  needs_first_outreach: number
  waiting_for_reply: number
  follow_up_soon: number
  needs_contact_research: number
  high_priority: number
  needs_enrichment: number
  ready_for_catalog_quote: number
}

export function computeDailySummary<T extends RhythmLeadRow>(
  rows: T[],
): DailySummaryCounts {
  const counts: DailySummaryCounts = {
    total: rows.length,
    needs_first_outreach: 0,
    waiting_for_reply: 0,
    follow_up_soon: 0,
    needs_contact_research: 0,
    high_priority: 0,
    needs_enrichment: 0,
    ready_for_catalog_quote: 0,
  }
  for (const row of rows) {
    for (const c of classifyFollowUpCategories(row)) {
      counts[c] += 1
    }
  }
  return counts
}

export function isOperationFilter(key: string): key is OperationFilterKey {
  return OPERATION_FILTER_OPTIONS.some((o) => o.key === key)
}

export function filterByRhythmCategory<T extends RhythmLeadRow>(
  rows: T[],
  filter: OperationFilterKey,
): T[] {
  if (filter === 'today_focus') {
    return rows.filter((r) => {
      const cats = classifyFollowUpCategories(r)
      return TODAY_FOCUS_CATEGORIES.some((c) => cats.includes(c))
    })
  }
  return rows.filter((r) => classifyFollowUpCategories(r).includes(filter))
}

export function isSegmentFilterKey(key: string): boolean {
  return SEGMENT_FILTER_OPTIONS.some((o) => o.key === key)
}

export type RecommendedAction = {
  companyName: string
  action: string
  reason: string
  score: number
}

export function recommendTopActions<T extends RhythmLeadRow & { companyName: string }>(
  rows: T[],
  limit = 10,
): RecommendedAction[] {
  const priority: FollowUpCategory[] = [
    'high_priority',
    'needs_first_outreach',
    'waiting_for_reply',
    'follow_up_soon',
    'needs_contact_research',
    'ready_for_catalog_quote',
    'needs_enrichment',
  ]
  const scored = rows.map((row) => {
    const cats = classifyFollowUpCategories(row)
    let rank = priority.length
    for (let i = 0; i < priority.length; i++) {
      if (cats.includes(priority[i])) {
        rank = i
        break
      }
    }
    const primary = primaryStatusBadge(cats)
    const reason = primary ? STATUS_BADGE_LABELS[primary] : 'Review queue'
    const action =
      row.nextAction !== NO_NEXT_ACTION ? row.nextAction : 'Set next action in Lead Intelligence'
    return { row, rank, reason, action }
  })
  scored.sort((a, b) => {
    if (a.rank !== b.rank) return a.rank - b.rank
    return b.row.score - a.row.score
  })
  return scored.slice(0, limit).map(({ row, reason, action }) => ({
    companyName: row.companyName,
    action,
    reason,
    score: row.score,
  }))
}
