/** D5.7 — follow-up scheduling helpers (frontend). */

export type DueStatus =
  | 'no_follow_up_date'
  | 'overdue'
  | 'due_today'
  | 'due_soon'
  | 'scheduled'

export type DueQueueFilterKey =
  | 'all'
  | 'overdue'
  | 'due_today'
  | 'due_soon'
  | 'no_follow_up_date'
  | 'scheduled'
  | 'waiting_reply'

export const DUE_QUEUE_FILTER_OPTIONS: { key: DueQueueFilterKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'overdue', label: 'Overdue' },
  { key: 'due_today', label: 'Due Today' },
  { key: 'due_soon', label: 'Due Soon' },
  { key: 'no_follow_up_date', label: 'No Follow-up Date' },
  { key: 'scheduled', label: 'Scheduled' },
  { key: 'waiting_reply', label: 'Waiting Reply' },
]

export const DUE_STATUS_LABELS: Record<DueStatus, string> = {
  no_follow_up_date: 'No date',
  overdue: 'Overdue',
  due_today: 'Due today',
  due_soon: 'Due soon',
  scheduled: 'Scheduled',
}

export const FOLLOW_UP_SCHEDULER_SAFETY =
  'This only schedules a manual follow-up inside intelliOffice. It does not send messages or create calendar events.'

export function formatDateIso(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function addDays(base: Date, days: number): string {
  const d = new Date(base)
  d.setDate(d.getDate() + days)
  return formatDateIso(d)
}

export function quickFollowUpDates(today: Date = new Date()) {
  return {
    tomorrow: addDays(today, 1),
    in3Days: addDays(today, 3),
    in5Days: addDays(today, 5),
    nextWeek: addDays(today, 7),
  }
}

export function dueStatusTagType(status: DueStatus | string): '' | 'success' | 'warning' | 'info' | 'danger' {
  if (status === 'overdue') return 'danger'
  if (status === 'due_today') return 'warning'
  if (status === 'due_soon') return 'warning'
  if (status === 'scheduled') return 'info'
  return ''
}

export type FollowUpRowLike = {
  leadId: string
  dueStatus?: DueStatus | string
  waitingReply?: boolean
}

export function filterByDueQueue<T extends FollowUpRowLike>(
  rows: T[],
  filter: DueQueueFilterKey,
  waitingByLead: Record<string, boolean>,
): T[] {
  if (filter === 'all') return rows
  if (filter === 'waiting_reply') {
    return rows.filter((r) => waitingByLead[r.leadId])
  }
  return rows.filter((r) => (r.dueStatus || 'no_follow_up_date') === filter)
}

export function formatDaysUntilDue(days: number | null | undefined): string {
  if (days == null) return '—'
  if (days < 0) return `${Math.abs(days)}d overdue`
  if (days === 0) return 'Today'
  return `${days}d`
}
