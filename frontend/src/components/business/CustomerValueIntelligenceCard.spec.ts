/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import CustomerValueIntelligenceCard from './CustomerValueIntelligenceCard.vue'
import { fetchCustomerValueIntelligence, type CustomerValueIntelligence } from '@/api/dashboard'

vi.mock('@/api/dashboard', () => ({
  fetchCustomerValueIntelligence: vi.fn(),
}))

const payload: CustomerValueIntelligence = {
  items: [
    {
      company_id: 'company-1',
      customer_name: 'D8.3 Multi-Partner Demo Account',
      value_tier: 'active_prospect',
      value_score: 37,
      priority: 'P2',
      historical_quote_amount: 19680,
      won_order_amount: 19680,
      weighted_pipeline_amount: 0,
      quote_count: 1,
      order_count: 1,
      opportunity_count: 0,
      conversion_rate: 1,
      repeat_business_count: 0,
      partner_focus: ['HOSUN Lifting Systems', 'JOOBOO Education Furniture'],
      product_focus: ['lifting columns', 'education furniture', 'desk frames', 'project furniture'],
      customer_decision_factors: ['load', 'stability', 'noise', 'school procurement timing'],
      active_risks: ['Confirm lifting-system ETD', 'Education furniture finish sample'],
      recommended_reason: 'Value at risk: resolve delivery and feedback before pursuing repeat business.',
      next_action: 'Review quote learning and decide whether this account deserves a new campaign touch.',
      future_revenue_signal: 'quote_reactivation',
      project_scale: 'mid-size project',
      referral_value: 'needs_relationship_proof',
      commercial_quality: {
        tier: 'value_at_risk',
        service_burden: 'high_service_burden',
        management_answer: 'Value at risk because feedback remains unresolved.',
      },
      service_burden: 'high_service_burden',
      unresolved_feedback_count: 11,
    },
  ],
  summary: {
    total_accounts: 1,
    strategic_accounts: 0,
    growth_accounts: 0,
    active_prospects: 1,
    weighted_pipeline_amount: 0,
    won_order_amount: 19680,
    open_quote_amount: 0,
    healthy_revenue_proxy: 19680,
    commercial_quality_leader_count: 0,
    service_burden_account_count: 1,
  },
  commercial_quality_leaders: [],
  service_burden_accounts: [],
  management_questions: {
    who_to_follow: ['D8.3 Multi-Partner Demo Account'],
    why_follow: ['Resolve delivery and feedback first.'],
    what_is_commercially_healthy: [],
    which_value_is_at_risk: [],
    future_revenue_from: [],
  },
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

describe('CustomerValueIntelligenceCard', () => {
  beforeEach(() => {
    vi.mocked(fetchCustomerValueIntelligence).mockReset()
    vi.mocked(fetchCustomerValueIntelligence).mockResolvedValue(payload)
  })

  it('renders customer value intelligence for the current company', async () => {
    const wrapper = mount(CustomerValueIntelligenceCard, {
      props: {
        companyId: 'company-1',
        companyName: 'D8.3 Multi-Partner Demo Account',
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    await flushPromises()

    expect(fetchCustomerValueIntelligence).toHaveBeenCalledWith(80)
    expect(wrapper.text()).toContain('客户价值智能')
    expect(wrapper.text()).toContain('P2 补商业证据')
    expect(wrapper.text()).toContain('$19,680')
    expect(wrapper.text()).toContain('100%')
    expect(wrapper.text()).toContain('HOSUN Lifting Systems')
    expect(wrapper.text()).toContain('JOOBOO Education Furniture')
    expect(wrapper.text()).toContain('load')
    expect(wrapper.text()).toContain('school procurement timing')
    expect(wrapper.text()).toContain('客户价值存在风险')
    expect(wrapper.text()).toContain('Review quote learning')
    expect(wrapper.text()).toContain('不暴露成本、利润')
  })
})
