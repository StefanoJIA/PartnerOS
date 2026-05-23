import { http } from '@/api/http'

export type DailyWorkSummaryCounts = {
  manual_outreach_sent: number
  contact_research_updates: number
  follow_ups_scheduled: number
  drafts_generated: number | null
  leads_touched: number
  overdue_remaining: number
  due_today_remaining: number
  due_soon: number
  needs_contact_research: number
  high_priority_remaining: number
}

export type DailyWorkHighlight = {
  lead_id: string
  company_name: string
  action: string
  next_action: string | null
}

export type DailyWorkTomorrowFocus = {
  lead_id: string
  company_name: string
  reason: string
  next_action: string | null
}

export type DailyWorkSummary = {
  date: string
  summary: DailyWorkSummaryCounts
  highlights: DailyWorkHighlight[]
  tomorrow_focus: DailyWorkTomorrowFocus[]
  copyable_summary: string
  warnings: string[]
  degraded: boolean
}

export async function fetchDailyWorkSummary(date?: string): Promise<DailyWorkSummary> {
  const params = date ? { date } : undefined
  const { data } = await http.get<DailyWorkSummary>('/a-domain/daily-work-summary', { params })
  return {
    ...data,
    highlights: data.highlights ?? [],
    tomorrow_focus: data.tomorrow_focus ?? [],
    warnings: data.warnings ?? [],
  }
}
