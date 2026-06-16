/**
 * @vitest-environment happy-dom
 */
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import CommercialMemoryPanel from './CommercialMemoryPanel.vue'
import { fetchAccount360Detail, fetchCustomerValueDetail } from '@/api/dashboard'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/api/dashboard', () => ({
  fetchAccount360Detail: vi.fn(),
  fetchCustomerValueDetail: vi.fn(),
}))

const accountDetail = {
  account_key: 'company:company-1',
  customer_name: 'HOSUN target account',
  current_stage: 'Quotation',
  priority: 'P1',
  partner_focus: ['HOSUN'],
  product_focus: ['lifting systems', 'desk frames', 'heavy-duty supply'],
  source_counts: { quote: 2, order: 1, feedback: 1 },
  commercial_value: {
    repeat_business_signal: 'Delivered order plus feedback creates repeat-business motion.',
  },
  detail_summary: {
    source_paths: ['/quotes/quote-1', '/orders/order-1'],
  },
  commercial_questions: {
    what_converts: ['load range', 'noise claim', 'delivery window'],
    why_win_or_lose: ['Won when load and delivery evidence were explicit.'],
  },
  commercial_asset_coverage: {
    lead: true,
    opportunity: true,
    quote: true,
    order: true,
    feedback: true,
    win_loss: true,
  },
  object_timeline: [
    {
      source_type: 'quote',
      quote_number: 'Q-100',
      current_signal: 'Quote focused on lifting systems and warranty wording.',
      path: '/quotes/quote-1',
    },
  ],
  next_commercial_motion: {
    next_action: 'Use win/loss evidence to prepare the next HOSUN quote follow-up.',
  },
  customer_safe_boundary: 'Internal commercial memory only.',
  safety: { external_message_sent: false, forbidden_fields_exposed: false },
}

const valueDetail = {
  company_id: 'company-1',
  customer_name: 'HOSUN target account',
  summary: {
    value_tier: 'Strategic growth account',
    weighted_pipeline_amount: 24000,
    won_order_amount: 12000,
    quote_to_order_rate: 0.5,
  },
  commercial_quality: { score: 82 },
  project_scale: 'project-based buyer',
  strategic_value: 'High fit for lifting systems repeat motion.',
  referral_value: 'Could introduce heavy-duty supply project contacts.',
  future_revenue_signal: 'Near-term quote plus delivered order support repeat potential.',
  partner_focus: ['HOSUN'],
  product_focus: ['lifting columns'],
  customer_decision_factors: ['load', 'stability', 'certification'],
  active_risks: ['warranty wording needs business approval'],
  quote_evidence: [
    {
      quote_number: 'Q-100',
      commercial_lesson: 'Certification wording affected quote confidence.',
      path: '/quotes/quote-1',
    },
  ],
  order_evidence: [
    {
      order_number: 'O-100',
      signal: 'Delivered order validates delivery window.',
      path: '/orders/order-1',
    },
  ],
  opportunity_evidence: [
    {
      opportunity_name: 'Desk frame project',
      reason: 'Customer asked for heavy-duty lifting supply.',
      path: '/growth-operations',
    },
  ],
  feedback_evidence: [
    {
      feedback_number: 'FB-100',
      signal: 'Packaging feedback should feed Market Response.',
      path: '/feedback-tickets',
    },
  ],
  win_loss_learning: {
    lessons: ['Lost risk rises when certification proof is not ready.'],
  },
  related_account: {},
  management_questions: {
    who_to_follow: 'Follow HOSUN project buyer first.',
    why_follow: 'Quote and delivered order both show repeat potential.',
    next_quote_guidance: 'Prepare load, noise and certification proof before next quote.',
  },
  source_paths: ['/companies/company-1'],
  next_action: 'Confirm customer-safe load and certification wording.',
  customer_safe_boundary: 'No cost, margin or supplier-private fields.',
  safety: { external_message_sent: false, forbidden_fields_exposed: false },
}

describe('CommercialMemoryPanel', () => {
  beforeEach(() => {
    push.mockReset()
    vi.mocked(fetchAccount360Detail).mockReset()
    vi.mocked(fetchCustomerValueDetail).mockReset()
    vi.mocked(fetchAccount360Detail).mockResolvedValue(accountDetail)
    vi.mocked(fetchCustomerValueDetail).mockResolvedValue(valueDetail)
  })

  it('renders account commercial memory with value, win/loss, evidence, and safety boundary', async () => {
    const wrapper = mount(CommercialMemoryPanel, {
      props: { companyId: 'company-1', companyName: 'HOSUN target account' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(fetchAccount360Detail).toHaveBeenCalledWith('company:company-1')
    expect(fetchCustomerValueDetail).toHaveBeenCalledWith('company-1')
    expect(wrapper.text()).toContain('商业记忆 / Account 360')
    expect(wrapper.text()).toContain('Strategic growth account')
    expect(wrapper.text()).toContain('$24,000')
    expect(wrapper.text()).toContain('Use win/loss evidence to prepare the next HOSUN quote follow-up.')
    expect(wrapper.text()).toContain('Won when load and delivery evidence were explicit.')
    expect(wrapper.text()).toContain('Lost risk rises when certification proof is not ready.')
    expect(wrapper.text()).toContain('load')
    expect(wrapper.text()).toContain('warranty wording needs business approval')
    expect(wrapper.text()).toContain('报价')
    expect(wrapper.text()).toContain('订单')
    expect(wrapper.text()).toContain('反馈')
    expect(wrapper.text()).toContain('不展示成本、利润、供应商私密信息或 token')
  })

  it('keeps Account 360 visible when customer value detail is not available yet', async () => {
    vi.mocked(fetchCustomerValueDetail).mockRejectedValue(new Error('Request failed with status code 404'))

    const wrapper = mount(CommercialMemoryPanel, {
      props: { companyId: 'company-1', companyName: 'HOSUN target account' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('商业记忆 / Account 360')
    expect(wrapper.text()).toContain('客户价值层级')
    expect(wrapper.text()).toContain('待判断')
    expect(wrapper.text()).toContain('Use win/loss evidence to prepare the next HOSUN quote follow-up.')
    expect(wrapper.text()).not.toContain('Request failed with status code 404')
  })
})
