import { http } from '@/api/http'

export type DailyOpsSummaryCounts = {
  total_leads: number
  overdue: number
  due_today: number
  due_soon: number
  high_priority: number
  needs_contact_research: number
  ready_for_outreach: number
  waiting_reply: number
  needs_enrichment: number
}

export type DailyOpsFocusItem = {
  lead_id: string
  company_name: string
  reason: string
  segments: string[]
  due_status: string
  next_action: string | null
  priority: string
  lead_score: number
}

export type DailyOpsQuickAction = {
  label: string
  path: string
}

export type DailyOpsSafety = {
  automatic_sending_enabled: boolean
  linkedin_automation_enabled: boolean
  outlook_integration_enabled: boolean
}

export type DailyOpsRecentActivity = {
  lead_id: string
  company_name: string
  type: string
  channel: string
  summary: string | null
  timestamp: string | null
  badge: string
  is_manual_send: boolean
  is_contact_research: boolean
  next_action?: string | null
  interaction_type?: string | null
}

export type DailyOpsRecentOutreach = DailyOpsRecentActivity

export type DailyOpsSummary = {
  summary: DailyOpsSummaryCounts
  today_focus: DailyOpsFocusItem[]
  recent_activity?: DailyOpsRecentActivity[]
  recent_manual_outreach?: DailyOpsRecentActivity[]
  recent_contact_research?: DailyOpsRecentActivity[]
  recent_outreach?: DailyOpsRecentOutreach[]
  quick_actions: DailyOpsQuickAction[]
  safety: DailyOpsSafety
  warnings: string[]
  degraded: boolean
}

export async function fetchDailyOpsSummary(): Promise<DailyOpsSummary> {
  const { data } = await http.get<DailyOpsSummary>('/a-domain/daily-ops-summary')
  return {
    ...data,
    recent_activity: data.recent_activity ?? [],
    recent_manual_outreach: data.recent_manual_outreach ?? [],
    recent_contact_research: data.recent_contact_research ?? [],
    recent_outreach: data.recent_outreach ?? data.recent_manual_outreach ?? [],
  }
}
