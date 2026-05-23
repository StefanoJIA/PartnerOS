/** Outreach timeline display helpers (D5.6). */

export const TIMELINE_SAFETY_NOTICE =
  'This timeline records manual actions only. intelliOffice does not send messages or automate LinkedIn / Outlook.'

export const TIMELINE_EMPTY_MESSAGE =
  'No outreach history yet. Generate a draft, send it manually, then mark it as sent.'

export function formatTimelineTimestamp(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return iso.slice(0, 16)
    return d.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso.slice(0, 16)
  }
}

export function interactionTypeBadgeType(
  type: string,
  isManualSend: boolean,
  isContactResearch: boolean,
): '' | 'success' | 'warning' | 'info' | 'primary' {
  if (isContactResearch) return 'warning'
  if (isManualSend) return 'success'
  if ((type || '').includes('linkedin')) return 'primary'
  return 'info'
}

export function followUpHintTagType(hint: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  const h = hint.toLowerCase()
  if (h.includes('needs contact research') || h.includes('needs first')) return 'danger'
  if (h.includes('waiting')) return 'info'
  if (h.includes('follow up')) return 'warning'
  if (h.includes('ready to prepare')) return 'success'
  return ''
}
