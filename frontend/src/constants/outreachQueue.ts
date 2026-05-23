/** Manual Outreach Queue helpers (D5.2.5 — frontend only). */

import type { SegmentFilterKey } from '@/constants/leadSegments'

export type QueueFilterKey =
  | SegmentFilterKey
  | 'high_score'
  | 'no_next_action'
  | 'needs_followup'

export type DraftStatus = 'none' | 'generated' | 'copied' | 'sent'

export const QUEUE_FILTER_OPTIONS: { key: QueueFilterKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'high_score', label: 'High Score' },
  { key: 'no_next_action', label: 'No Next Action' },
  { key: 'needs_followup', label: 'Needs Follow-up' },
  { key: 'lift_system_signal', label: 'Lifting' },
  { key: 'medical_vertical', label: 'Medical' },
  { key: 'education_vertical', label: 'Education' },
  { key: 'project_based_furniture', label: 'Project' },
  { key: 'general_office_furniture_only', label: 'General Office' },
]

export type ChannelRecommendation = {
  label: string
  channel: string
  productFocus: string
}

export function recommendChannel(
  segments: string[],
  contactEmail?: string | null,
  linkedinUrl?: string | null,
): ChannelRecommendation {
  const hasEmail = Boolean(contactEmail?.trim())
  const hasLinkedIn = Boolean(linkedinUrl?.trim())

  if (!hasEmail && !hasLinkedIn) {
    return { label: 'Enrich company / Find contact', channel: '', productFocus: 'general' }
  }

  if (segments.includes('lift_system_signal')) {
    if (hasLinkedIn) {
      return { label: 'LinkedIn connect', channel: 'linkedin_connect', productFocus: 'hosun_lifting' }
    }
    return { label: 'Email intro', channel: 'email_intro', productFocus: 'hosun_lifting' }
  }

  if (segments.includes('education_vertical')) {
    return { label: 'Email intro', channel: 'email_intro', productFocus: 'jooboo_education' }
  }

  if (segments.includes('medical_vertical')) {
    return { label: 'Email intro', channel: 'email_intro', productFocus: 'medical_workspace' }
  }

  if (segments.includes('project_based_furniture')) {
    if (hasEmail) {
      return { label: 'Email intro / Meeting proposal', channel: 'email_intro', productFocus: 'project_supply' }
    }
    return { label: 'LinkedIn follow-up', channel: 'linkedin_followup', productFocus: 'project_supply' }
  }

  if (hasEmail) {
    return { label: 'Email intro', channel: 'email_intro', productFocus: 'general' }
  }
  return { label: 'LinkedIn connect', channel: 'linkedin_connect', productFocus: 'general' }
}

export function touchpointTypeForChannel(channel: string): string {
  const map: Record<string, string> = {
    linkedin_connect: 'linkedin_connect_note',
    linkedin_followup: 'waiting_for_reply',
    email_intro: 'catalog_sent',
    email_followup: 'quotation_follow_up',
  }
  return map[channel] || 'follow_up'
}

export function followUpNextAction(channel: string, productFocus: string): string {
  if (channel === 'linkedin_connect') return 'Follow up in 5 days — waiting for LinkedIn connection reply'
  if (channel === 'linkedin_followup') return 'Follow up in 5 days — waiting for LinkedIn reply'
  if (channel === 'email_intro') {
    if (productFocus === 'jooboo_education') return 'Wait for reply — send education catalog if they respond'
    if (productFocus === 'medical_workspace') return 'Wait for reply — offer sample discussion if interested'
    return 'Follow up in 5 days — waiting for email reply'
  }
  if (channel === 'email_followup') return 'Wait for reply — prepare quotation if interested'
  return 'Follow up in 5 days'
}

export function buildManualSentSummary(params: {
  channel: string
  productFocus: string
  draftPreview: string
}): string {
  const preview = params.draftPreview.slice(0, 200).replace(/\s+/g, ' ')
  return (
    `[manually_sent=true] channel=${params.channel}; product_focus=${params.productFocus}; ` +
    `draft_preview="${preview}${params.draftPreview.length > 200 ? '…' : ''}"`
  )
}

export function filterQueueRows<T extends {
  score: number
  segments: string[]
  nextAction: string
  touchCount: number
}>(rows: T[], filter: QueueFilterKey): T[] {
  let out = [...rows]
  switch (filter) {
    case 'high_score':
      out = out.filter((r) => r.score >= 70)
      break
    case 'no_next_action':
      out = out.filter((r) => r.nextAction === 'No next action set.')
      break
    case 'needs_followup':
      out = out.filter((r) => r.nextAction !== 'No next action set.')
      break
    case 'all':
      break
    default:
      out = out.filter((r) => r.segments.includes(filter))
  }
  return out.sort((a, b) => {
    const aNoTouch = a.touchCount === 0 ? 1 : 0
    const bNoTouch = b.touchCount === 0 ? 1 : 0
    if (aNoTouch !== bNoTouch) return bNoTouch - aNoTouch
    const aHasNext = a.nextAction !== 'No next action set.' ? 1 : 0
    const bHasNext = b.nextAction !== 'No next action set.' ? 1 : 0
    if (aHasNext !== bHasNext) return bHasNext - aHasNext
    return b.score - a.score
  })
}

export function draftStatusLabel(status: DraftStatus): string {
  if (status === 'generated') return 'Draft generated'
  if (status === 'copied') return 'Copied'
  if (status === 'sent') return 'Marked sent'
  return '—'
}

export const OUTREACH_SAFETY_NOTICE =
  'intelliOffice only generates human-reviewed drafts. It does not send messages, scrape LinkedIn, or automate platform actions.'

export const MARK_AS_SENT_HINT =
  'Mark as Sent records that you manually sent this message outside intelliOffice.'
