/**
 * @vitest-environment happy-dom
 */
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import PartnerPerformanceCard from './PartnerPerformanceCard.vue'
import { fetchPartnerPerformanceIntelligence, type PartnerPerformanceIntelligence } from '@/api/dashboard'

vi.mock('@/api/dashboard', () => ({
  fetchPartnerPerformanceIntelligence: vi.fn(),
}))

const payload = {
  summary: {
    partner_count: 1,
    active_partner_count: 1,
    quote_support_amount: 120000,
    order_amount: 85000,
    risk_partner_count: 0,
    p1_partner_count: 1,
    feedback_issue_count: 1,
    quote_allocation_candidate_count: 1,
    pilot_candidate_count: 1,
    allocation_risk_count: 0,
  },
  items: [
    {
      partner_id: 'partner-hosun',
      partner_name: 'HOSUN Lifting Systems',
      product_focus: ['lifting systems', 'desk frames', 'lifting columns', 'heavy-duty supply'],
      quote_support_count: 4,
      win_rate: 0.5,
      order_amount: 85000,
      on_time_delivery_rate: 0.9,
      feedback_issue_count: 1,
      investment_priority: 'P1',
      health: 'proven_commercial_partner',
      allocation_fit: 'allocate_next_quotes',
      pilot_fit: 'pilot_candidate',
      allocation_score: 82,
      missing_inputs: ['certification summary needs business sign-off'],
      risk_signals: ['noise claim needs validation'],
      next_allocation_action: 'Allocate the next matching quote after load and certification wording are reviewed.',
      safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
    },
  ],
  top_investment_candidates: [],
  quote_allocation_candidates: [],
  pilot_candidates: [],
  allocation_risks: [],
  product_line_allocation: [
    {
      partner_name: 'HOSUN Lifting Systems',
      product_focus: 'lifting columns',
      allocation_fit: 'allocate_next_quotes',
      pilot_fit: 'pilot_candidate',
      win_rate: 0.5,
      feedback_issue_count: 1,
      next_action: 'Use HOSUN lifting columns for the next qualified heavy-duty project.',
    },
  ],
  delivery_or_feedback_risks: [],
  partner_scoreboard: [],
  management_questions: {},
  next_action: 'Use allocation fit before assigning the next quote.',
  customer_safe_boundary: 'Internal only',
  safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
} as unknown as PartnerPerformanceIntelligence

describe('PartnerPerformanceCard', () => {
  beforeEach(() => {
    vi.mocked(fetchPartnerPerformanceIntelligence).mockReset()
    vi.mocked(fetchPartnerPerformanceIntelligence).mockResolvedValue(payload)
  })

  it('renders object-level partner performance intelligence and allocation guidance', async () => {
    const wrapper = mount(PartnerPerformanceCard, {
      props: {
        partnerId: 'partner-hosun',
        partnerName: 'HOSUN Lifting Systems',
        brandName: 'HOSUN',
        productKeywords: ['desk frames', 'lifting columns'],
        quoteCount: 2,
        orderCount: 1,
      },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(fetchPartnerPerformanceIntelligence).toHaveBeenCalledWith(120)
    expect(wrapper.text()).toContain('Partner 绩效智能')
    expect(wrapper.text()).toContain('P1 投入/风险优先')
    expect(wrapper.text()).toContain('报价支持')
    expect(wrapper.text()).toContain('4')
    expect(wrapper.text()).toContain('赢单率')
    expect(wrapper.text()).toContain('50%')
    expect(wrapper.text()).toContain('$85,000')
    expect(wrapper.text()).toContain('可分配下一轮匹配报价')
    expect(wrapper.text()).toContain('可作为 pilot 候选')
    expect(wrapper.text()).toContain('lifting columns')
    expect(wrapper.text()).toContain('noise claim needs validation')
    expect(wrapper.text()).toContain('可分配下一轮匹配报价或 pilot 机会')
  })
})
