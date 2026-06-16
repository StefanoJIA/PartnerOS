/**
 * @vitest-environment happy-dom
 */
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RevenueForecastIntelligenceCard from './RevenueForecastIntelligenceCard.vue'
import { fetchRevenueForecastIntelligence, type RevenueForecastIntelligence } from '@/api/dashboard'

vi.mock('@/api/dashboard', () => ({
  fetchRevenueForecastIntelligence: vi.fn(),
}))

const payload: RevenueForecastIntelligence = {
  summary: {
    total_forecast_amount: 180000,
    total_weighted_amount: 124000,
    weighted_opportunity_amount: 100000,
    open_quote_amount: 30000,
    weighted_quote_amount: 24000,
    booked_backlog_amount: 20000,
    at_risk_weighted_amount: 18000,
    item_count: 3,
    high_probability_count: 1,
    high_risk_count: 1,
    committed_backlog_amount: 20000,
    forecastable_weighted_amount: 70000,
    manual_follow_up_weighted_amount: 24000,
    weak_signal_weighted_amount: 10000,
    forecast_quality_score: 72,
  },
  total_weighted_amount: 124000,
  open_quote_amount: 30000,
  weighted_quote_amount: 24000,
  at_risk_weighted_amount: 18000,
  forecast_items: [],
  high_probability_projects: [
    {
      source_type: 'opportunity',
      source_id: 'opp-1',
      name: 'HOSUN lifting systems pilot',
      customer_name: 'Project buyer',
      partner_focus: 'HOSUN',
      product_focus: ['lifting systems', 'desk frames', 'lifting columns'],
      probability: 82,
      weighted_amount: 70000,
      risk_level: 'medium',
      risk_reason: 'Needs validation for load, noise, warranty, certification, delivery, and installation wording.',
      next_action: 'Confirm customer-safe technical wording before quote revision.',
    },
  ],
  high_risk_projects: [
    {
      source_type: 'quote',
      source_id: 'quote-1',
      name: 'JOOBOO education furniture quote',
      customer_name: 'School procurement team',
      partner_focus: 'JOOBOO',
      product_focus: ['education furniture', 'school desks/chairs', 'project furniture'],
      probability: 55,
      weighted_amount: 18000,
      risk_level: 'high',
      risk_reason: 'Delivery consistency and resource needs remain unresolved.',
      next_action: 'Review delivery assumptions and feedback after use.',
    },
  ],
  committed_backlog: [],
  forecastable_revenue: [],
  manual_follow_up_revenue: [],
  weak_signal_revenue: [],
  revenue_bucket_mix: [
    { name: 'forecastable_pipeline', weighted_amount: 70000, amount: 90000, item_count: 1 },
    { name: 'manual_quote_follow_up', weighted_amount: 24000, amount: 30000, item_count: 1 },
  ],
  source_type_mix: [],
  forecast_by_partner: [
    { partner_focus: 'HOSUN', weighted_amount: 70000 },
    { partner_focus: 'JOOBOO', weighted_amount: 18000 },
    { partner_focus: 'future partner', weighted_amount: 10000 },
  ],
  forecast_by_product: [
    { product_focus: ['lifting systems', 'desk frames'] },
    { product_focus: ['education furniture', 'school desks/chairs'] },
  ],
  forecast_by_customer: [],
  future_revenue_sources: ['HOSUN lifting systems', 'JOOBOO education furniture'],
  management_questions: {},
  next_action: 'Separate high probability projects from risk revenue before weekly revenue decisions.',
  customer_safe_boundary: 'No cost or margin exposure.',
  safety: {
    external_message_sent: false,
    quote_status_changed: false,
    order_status_changed: false,
    raw_token_recorded: false,
    staging_validated: false,
    customer_forbidden_fields_exposed: false,
  },
}

describe('RevenueForecastIntelligenceCard', () => {
  beforeEach(() => {
    vi.mocked(fetchRevenueForecastIntelligence).mockReset()
    vi.mocked(fetchRevenueForecastIntelligence).mockResolvedValue(payload)
  })

  it('renders revenue forecast intelligence for growth operations', async () => {
    const wrapper = mount(RevenueForecastIntelligenceCard, {
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    expect(fetchRevenueForecastIntelligence).toHaveBeenCalledWith(80)
    expect(wrapper.text()).toContain('Revenue Forecast Intelligence')
    expect(wrapper.text()).toContain('$180,000')
    expect(wrapper.text()).toContain('$124,000')
    expect(wrapper.text()).toContain('有高风险收入')
    expect(wrapper.text()).toContain('HOSUN lifting systems pilot')
    expect(wrapper.text()).toContain('JOOBOO education furniture quote')
    expect(wrapper.text()).toContain('lifting systems')
    expect(wrapper.text()).toContain('school desks/chairs')
    expect(wrapper.text()).toContain('最容易成交')
    expect(wrapper.text()).toContain('需要人工复核')
    expect(wrapper.text()).toContain('不自动发送外部消息')
    expect(wrapper.text()).toContain('不暴露成本、利润')
  })
})
