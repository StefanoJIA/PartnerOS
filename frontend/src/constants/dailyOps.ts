/** D5.8 / D5.9 — daily operations dashboard copy. */

export const DAILY_OPS_TITLE = 'Daily Operations Command Center'

export const DAILY_OPS_SUBTITLE =
  "Review today's manual outreach, follow-up, and lead cleanup priorities."

export const DAILY_OPS_SAFETY_NOTE =
  'All outreach remains human-reviewed. intelliOffice does not send messages automatically.'

export const DAILY_OPS_DEGRADED_HINT =
  'Daily operations unavailable. Check backend and database status.'

export const RECENT_OUTREACH_EMPTY = 'No recent manual outreach yet.'

export const RECENT_RESEARCH_EMPTY = 'No recent contact research yet.'

export const RECENT_ACTIVITY_EMPTY = 'No recent activity yet.'

/** Summary card → lead-intelligence filter deep links */
export const SUMMARY_CARD_LINKS: Record<string, string> = {
  Overdue: '/lead-intelligence?filter=overdue',
  'Due Today': '/lead-intelligence?filter=due_today',
  'Due Soon': '/lead-intelligence?filter=due_soon',
  'High Priority': '/lead-intelligence',
  'Needs Contact Research': '/lead-intelligence?filter=needs_contact_research',
  'Ready for Outreach': '/lead-intelligence?filter=ready_for_outreach',
  'Waiting Reply': '/lead-intelligence?filter=waiting_reply',
  'Needs Enrichment': '/lead-intelligence?filter=missing_enrichment',
}
