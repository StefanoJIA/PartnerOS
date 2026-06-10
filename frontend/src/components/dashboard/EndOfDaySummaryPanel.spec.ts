/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import EndOfDaySummaryPanel from '@/components/dashboard/EndOfDaySummaryPanel.vue'
import {
  EOD_SAFETY_NOTE,
  EOD_TITLE,
  EOD_EMPTY_HIGHLIGHTS,
} from '@/constants/dailyWorkSummary'
import * as dailyWork from '@/api/dailyWorkSummary'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/api/dailyWorkSummary', () => ({
  fetchDailyWorkSummary: vi.fn(),
}))

const mockData = {
  date: '2026-05-23',
  summary: {
    manual_outreach_sent: 3,
    contact_research_updates: 2,
    follow_ups_scheduled: 4,
    drafts_generated: null,
    leads_touched: 6,
    overdue_remaining: 2,
    due_today_remaining: 1,
    due_soon: 5,
    needs_contact_research: 12,
    high_priority_remaining: 18,
  },
  highlights: [
    {
      lead_id: 'l1',
      company_name: 'SWC Office Furniture',
      action: 'Manual email intro marked as sent',
      next_action: 'Follow up in 5 days',
    },
  ],
  tomorrow_focus: [
    {
      lead_id: 'l2',
      company_name: 'Dancker',
      reason: 'Due soon',
      next_action: 'Ask about FF&E procurement',
    },
  ],
  copyable_summary: 'Daily intelliOffice Summary — 2026-05-23',
  warnings: [],
  degraded: false,
}

describe('EndOfDaySummaryPanel', () => {
  beforeEach(() => {
    vi.mocked(dailyWork.fetchDailyWorkSummary).mockReset()
    push.mockReset()
    vi.stubGlobal('navigator', {
      ...navigator,
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    })
  })

  it('renders panel title', async () => {
    vi.mocked(dailyWork.fetchDailyWorkSummary).mockResolvedValue(mockData)
    const wrapper = mount(EndOfDaySummaryPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain(EOD_TITLE)
  })

  it('renders summary cards', async () => {
    vi.mocked(dailyWork.fetchDailyWorkSummary).mockResolvedValue(mockData)
    const wrapper = mount(EndOfDaySummaryPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('人工触达')
    expect(wrapper.text()).toContain('3')
  })

  it('renders highlights and tomorrow focus', async () => {
    vi.mocked(dailyWork.fetchDailyWorkSummary).mockResolvedValue(mockData)
    const wrapper = mount(EndOfDaySummaryPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('SWC Office Furniture')
    expect(wrapper.text()).toContain('Dancker')
  })

  it('renders empty highlights state', async () => {
    vi.mocked(dailyWork.fetchDailyWorkSummary).mockResolvedValue({ ...mockData, highlights: [] })
    const wrapper = mount(EndOfDaySummaryPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain(EOD_EMPTY_HIGHLIGHTS)
  })

  it('renders safety note', async () => {
    vi.mocked(dailyWork.fetchDailyWorkSummary).mockResolvedValue(mockData)
    const wrapper = mount(EndOfDaySummaryPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain(EOD_SAFETY_NOTE)
  })

  it('date change triggers fetch', async () => {
    vi.mocked(dailyWork.fetchDailyWorkSummary).mockResolvedValue(mockData)
    const wrapper = mount(EndOfDaySummaryPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    const vm = wrapper.vm as { selectedDate: string; load: () => Promise<void> }
    vm.selectedDate = '2026-05-22'
    await vm.load()
    expect(dailyWork.fetchDailyWorkSummary).toHaveBeenCalledWith('2026-05-22')
  })

  it('copy summary works', async () => {
    vi.mocked(dailyWork.fetchDailyWorkSummary).mockResolvedValue(mockData)
    const wrapper = mount(EndOfDaySummaryPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    const vm = wrapper.vm as { copySummary: () => Promise<void> }
    await vm.copySummary()
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockData.copyable_summary)
  })

  it('error state does not white screen', async () => {
    vi.mocked(dailyWork.fetchDailyWorkSummary).mockRejectedValue(new Error('fail'))
    const wrapper = mount(EndOfDaySummaryPanel, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('日终总结暂不可用')
  })
})
