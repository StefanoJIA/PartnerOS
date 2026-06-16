/**
 * @vitest-environment happy-dom
 */
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import QuoteWinLossIntelligenceCard from './QuoteWinLossIntelligenceCard.vue'
import { fetchWinLossIntelligenceDashboard, type WinLossIntelligenceDashboard } from '@/api/dashboard'

vi.mock('@/api/dashboard', () => ({
  fetchWinLossIntelligenceDashboard: vi.fn(),
}))

const payload = {
  summary: {
    total: 2,
    won: 1,
    lost: 1,
    open_or_unclear: 0,
    win_rate: 0.5,
    commercial_amount: 120000,
    opportunity_records: 1,
    quote_learning_records: 1,
  },
  items: [
    {
      source_type: 'quote_learning',
      source_id: 'learn-1',
      quote_id: 'quote-1',
      quote_number: 'Q-100',
      outcome: 'lost',
      customer: 'Strategic desk buyer',
      partner_focus: 'HOSUN',
      product_focus: ['lifting systems', 'desk frames'],
      quote_value: 65000,
      commercial_amount: 65000,
      reason_category: 'competition_or_alternative',
      decision_factors: ['noise proof missing', 'competitor claims faster delivery', 'desk frames'],
      competitor_signal: 'local competitor claims shorter delivery',
      commercial_lesson: 'Lost because noise and delivery proof were not convincing.',
      next_quote_guidance: 'Capture competitor positioning and adjust differentiation for lifting systems.',
      path: '/quotes/quote-1',
      safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
    },
    {
      source_type: 'opportunity',
      source_id: 'opp-1',
      outcome: 'won',
      customer: 'Industrial workstation account',
      partner_focus: 'HOSUN',
      product_focus: ['lifting columns'],
      commercial_amount: 55000,
      reason_category: 'won_reason',
      decision_factors: ['validated load range', 'warranty support'],
      competitor_signal: 'competitor not recorded',
      commercial_lesson: 'Won after load range was validated.',
      next_quote_guidance: 'Use the winning reason for the next lifting columns quote.',
      path: '/growth-operations',
      safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
    },
  ],
  reason_clusters: [],
  partner_rollup: [],
  product_rollup: [],
  decision_factor_rows: [],
  competitor_signals: ['local competitor claims shorter delivery'],
  management_questions: {},
  next_action: 'Review win/loss factors.',
  customer_safe_boundary: 'Internal only',
  safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
} as unknown as WinLossIntelligenceDashboard

describe('QuoteWinLossIntelligenceCard', () => {
  beforeEach(() => {
    vi.mocked(fetchWinLossIntelligenceDashboard).mockReset()
    vi.mocked(fetchWinLossIntelligenceDashboard).mockResolvedValue(payload)
  })

  it('renders matched win/loss lessons for the current quote', async () => {
    const wrapper = mount(QuoteWinLossIntelligenceCard, {
      props: {
        quoteId: 'quote-1',
        quoteNumber: 'Q-100',
        customerName: 'Strategic desk buyer',
        partnerFocus: 'HOSUN',
        productKeywords: ['lifting systems', 'desk frames'],
      },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(fetchWinLossIntelligenceDashboard).toHaveBeenCalledWith(160)
    expect(wrapper.text()).toContain('Win/Loss 商业经验库')
    expect(wrapper.text()).toContain('复核丢单经验')
    expect(wrapper.text()).toContain('匹配经验')
    expect(wrapper.text()).toContain('50%')
    expect(wrapper.text()).toContain('Lost because noise and delivery proof were not convincing.')
    expect(wrapper.text()).toContain('记录竞争定位，并强化当前产品/Partner 的差异化表达。')
    expect(wrapper.text()).toContain('local competitor claims shorter delivery')
    expect(wrapper.text()).toContain('不自动发送外部消息')
    expect(wrapper.text()).toContain('不把成本、利润、供应商私密备注')
  })
})
