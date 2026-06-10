/** D5.8 / D5.9 — daily operations dashboard copy. */

export const DAILY_OPS_TITLE = '每日运营指挥台'

export const DAILY_OPS_SUBTITLE =
  '集中查看今日人工触达、跟进和线索清理优先级。'

export const DAILY_OPS_SAFETY_NOTE =
  '所有客户触达都需要人工审查。intelliOffice 不会自动发送消息。'

export const DAILY_OPS_DEGRADED_HINT =
  '每日运营数据暂不可用，请检查 backend 和数据库状态。'

export const RECENT_OUTREACH_EMPTY = '暂无近期人工触达记录。'

export const RECENT_RESEARCH_EMPTY = '暂无近期联系人调研记录。'

export const RECENT_ACTIVITY_EMPTY = '暂无近期活动。'

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
