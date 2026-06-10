/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import DailyOperationsPanel from '@/components/dashboard/DailyOperationsPanel.vue'
import {
  DAILY_OPS_DEGRADED_HINT,
  DAILY_OPS_SAFETY_NOTE,
  DAILY_OPS_TITLE,
  RECENT_OUTREACH_EMPTY,
} from '@/constants/dailyOps'
import * as dailyOps from '@/api/dailyOps'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/api/dailyOps', () => ({
  fetchDailyOpsSummary: vi.fn(),
}))

vi.mock('@/api/system', () => ({
  fetchLegacyHealth: vi.fn().mockResolvedValue({ status: 'ok', database_status: 'ready' }),
  fetchSystemReadiness: vi.fn().mockResolvedValue({ data: { database_ready: true } }),
}))

const mockSummary = {
  summary: {
    total_leads: 5,
    overdue: 2,
    due_today: 1,
    due_soon: 3,
    high_priority: 2,
    needs_contact_research: 4,
    ready_for_outreach: 1,
    waiting_reply: 1,
    needs_enrichment: 3,
  },
  today_focus: [
    {
      lead_id: 'lead-1',
      company_name: 'Acme Lift',
      reason: 'Overdue follow-up',
      segments: ['lift_system_signal'],
      due_status: 'overdue',
      next_action: 'Follow up with quote',
      priority: 'high',
      lead_score: 85,
    },
  ],
  recent_activity: [],
  recent_manual_outreach: [
    {
      lead_id: 'lead-1',
      company_name: 'Acme Lift',
      type: 'email_intro',
      channel: 'email',
      summary: 'Marked sent',
      timestamp: '2026-05-22T10:00:00Z',
      badge: 'Manual sent',
      is_manual_send: true,
      is_contact_research: false,
    },
  ],
  recent_contact_research: [],
  recent_outreach: [],
  quick_actions: [
    { label: 'Import Leads', path: '/lead-intake' },
    { label: 'System Health', path: '/system-health' },
  ],
  safety: {
    automatic_sending_enabled: false,
    linkedin_automation_enabled: false,
    outlook_integration_enabled: false,
  },
  warnings: [],
  degraded: false,
}

const mountPanel = () =>
  mount(DailyOperationsPanel, {
    global: {
      plugins: [ElementPlus],
      stubs: {
        RouterLink: {
          template: '<a><slot /></a>',
        },
      },
    },
  })

describe('DailyOperationsPanel', () => {
  beforeEach(() => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockReset()
    push.mockReset()
  })

  it('renders daily operations title', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mountPanel()
    await flushPromises()
    expect(wrapper.text()).toContain(DAILY_OPS_TITLE)
  })

  it('renders summary cards', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mountPanel()
    await flushPromises()
    expect(wrapper.text()).toContain('已逾期')
    expect(wrapper.text()).toContain('今日到期')
    expect(wrapper.text()).toContain('2')
  })

  it('renders quick actions', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mountPanel()
    await flushPromises()
    expect(wrapper.text()).toContain('快捷动作')
    expect(wrapper.text()).toContain('Import Leads')
    expect(wrapper.text()).toContain('System Health')
  })

  it('renders safety note', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mountPanel()
    await flushPromises()
    expect(wrapper.text()).toContain(DAILY_OPS_SAFETY_NOTE)
  })

  it('renders today focus list', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mountPanel()
    await flushPromises()
    expect(wrapper.text()).toContain('今日重点')
    expect(wrapper.text()).toContain('Acme Lift')
    expect(wrapper.text()).toContain('打开线索')
  })

  it('renders recent activity', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mountPanel()
    await flushPromises()
    expect(wrapper.text()).toContain('近期人工触达')
    expect(wrapper.text()).toContain('已人工发送')
  })

  it('renders empty recent activity state', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue({
      ...mockSummary,
      recent_manual_outreach: [],
      recent_contact_research: [],
      recent_outreach: [],
    })
    const wrapper = mountPanel()
    await flushPromises()
    expect(wrapper.text()).toContain(RECENT_OUTREACH_EMPTY)
  })

  it('renders error state', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockRejectedValue(new Error('network'))
    const wrapper = mountPanel()
    await flushPromises()
    expect(wrapper.text()).toContain('每日运营数据暂不可用')
  })

  it('renders degraded warning', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue({
      ...mockSummary,
      degraded: true,
      warnings: [DAILY_OPS_DEGRADED_HINT],
      today_focus: [],
      summary: { ...mockSummary.summary, overdue: 0 },
    })
    const wrapper = mountPanel()
    await flushPromises()
    expect(wrapper.text()).toContain('降级模式')
  })
})
