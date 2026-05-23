/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import DailyOperationsPanel from '@/components/dashboard/DailyOperationsPanel.vue'
import { DAILY_OPS_DEGRADED_HINT, DAILY_OPS_SAFETY_NOTE } from '@/constants/dailyOps'
import * as dailyOps from '@/api/dailyOps'

vi.mock('@/api/dailyOps', () => ({
  fetchDailyOpsSummary: vi.fn(),
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

describe('DailyOperationsPanel', () => {
  beforeEach(() => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockReset()
  })

  it('renders Daily Operations title', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mount(DailyOperationsPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Daily Operations')
  })

  it('renders summary cards', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mount(DailyOperationsPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Overdue')
    expect(wrapper.text()).toContain('Due Today')
    expect(wrapper.text()).toContain('2')
  })

  it('renders quick actions', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mount(DailyOperationsPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Quick Actions')
    expect(wrapper.text()).toContain('Import Leads')
    expect(wrapper.text()).toContain('System Health')
  })

  it('renders safety note', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mount(DailyOperationsPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain(DAILY_OPS_SAFETY_NOTE)
  })

  it('renders today focus list', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue(mockSummary)
    const wrapper = mount(DailyOperationsPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Today Focus')
    expect(wrapper.text()).toContain('Acme Lift')
    expect(wrapper.text()).toContain('Open Lead')
  })

  it('renders error state', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockRejectedValue(new Error('network'))
    const wrapper = mount(DailyOperationsPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Daily operations unavailable')
  })

  it('renders degraded warning', async () => {
    vi.mocked(dailyOps.fetchDailyOpsSummary).mockResolvedValue({
      ...mockSummary,
      degraded: true,
      warnings: [DAILY_OPS_DEGRADED_HINT],
      today_focus: [],
      summary: { ...mockSummary.summary, overdue: 0 },
    })
    const wrapper = mount(DailyOperationsPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Degraded mode')
  })
})
