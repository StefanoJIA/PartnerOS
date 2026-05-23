/** D5.10 — end-of-day summary copy and labels. */

export const EOD_TITLE = 'End-of-Day Summary'

export const EOD_SUBTITLE =
  "Review today's manual outreach and prepare tomorrow's follow-up."

export const EOD_SAFETY_NOTE =
  'This summary is generated from manual records only. intelliOffice does not send messages or automate external platforms.'

export const EOD_DEGRADED_HINT =
  'Daily work summary unavailable. Check backend and database status.'

export const EOD_EMPTY_HIGHLIGHTS = 'No recorded manual actions for this date.'

export const EOD_EMPTY_TOMORROW = 'No follow-up priorities queued.'

export const EOD_COPY_SUCCESS = 'Summary copied to clipboard.'

export function todayIsoDate(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
