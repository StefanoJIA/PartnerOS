/**
 * @vitest-environment happy-dom
 */
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AccountExecutionCard from './AccountExecutionCard.vue'
import { fetchCompanyWorkspace } from '@/api/objectWorkspaces'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/api/objectWorkspaces', () => ({
  fetchCompanyWorkspace: vi.fn(),
}))

const workspace = {
  business_execution: {
    account: {
      account_key: 'company-1',
      customer_name: 'HOSUN industrial account',
      current_stage: 'Repeat Business',
      priority: 'P1',
      owner: 'operator@example.com',
      partner_focus: 'HOSUN',
      product_focus: ['lifting systems', 'heavy-duty supply'],
      source_counts: { lead: 1, opportunity: 1, quote: 1, order: 1, feedback: 1 },
      active_paths: ['/companies/company-1'],
      open_blockers: ['Feedback needs owner response before repeat-business outreach.'],
      next_action: 'Use Account 360 to choose repeat outreach.',
      readiness_impact: ['repeat business', 'market response'],
      commercial_health: {
        health: 'after_sales_attention',
        score: 78,
        business_focus: 'repeat business',
        primary_stage: 'Repeat Business',
        primary_source_type: 'feedback',
        primary_source_id: 'fb-1',
        primary_path: '/feedback-tickets',
        primary_risk: 'feedback needs owner response',
        next_best_action: 'Resolve feedback before repeat outreach.',
        conversion_signal: 'won quote learning exists',
        delivery_signal: 'order delivered with shipment record',
        repeat_business_signal: 'feedback blocks repeat motion',
        business_questions: [],
        safety: { external_message_sent: false },
      },
      stage_progression: {
        health: 'needs_input',
        current_stage: 'After-Sales',
        next_stage: 'Repeat Business',
        blocks_next_stage: true,
        missing_inputs: ['feedback response summary'],
        recommended_action: 'Resolve feedback, then create repeat-business motion.',
        handoff_object: 'feedback_to_repeat_business',
        recommended_entry_path: '/feedback-tickets',
        readiness_impact: ['repeat business'],
        why_now: 'The account has delivery and feedback history.',
        safety: { external_message_sent: false },
      },
    },
    lifecycle: [
      {
        id: 'lead-1',
        source_type: 'lead',
        lifecycle_stage: 'Lead',
        current_signal: 'Lead stage: Qualified.',
        next_action: 'Confirm project timing.',
        path: '/leads/lead-1',
      },
      {
        id: 'opp-1',
        source_type: 'opportunity',
        lifecycle_stage: 'Opportunity',
        current_signal: 'Opportunity stage: negotiation; probability: 80%.',
        next_action: 'Confirm competitor and quote inputs.',
        path: '/growth-operations',
      },
      {
        id: 'quote-1',
        source_type: 'quote',
        lifecycle_stage: 'Quotation',
        current_signal: 'Quote Q-100; status: sent; versions: 2.',
        next_action: 'Record won/lost learning.',
        path: '/quotes/quote-1',
      },
      {
        id: 'order-1',
        source_type: 'order',
        lifecycle_stage: 'Delivery',
        current_signal: 'Order status: confirmed; production milestones: 2; shipments: 1.',
        next_action: 'Review delivery confidence.',
        path: '/orders/order-1',
      },
      {
        id: 'fb-1',
        source_type: 'feedback',
        lifecycle_stage: 'After-Sales',
        current_signal: 'Feedback FB-1; status: in_review; priority: high.',
        next_action: 'Resolve feedback and feed Market Response.',
        blocker: 'Feedback needs owner response before repeat-business outreach.',
        path: '/feedback-tickets',
      },
    ],
    safety: {
      external_message_sent: false,
      quote_status_changed: false,
      order_status_changed: false,
      customer_forbidden_fields_exposed: false,
    },
  },
}

describe('AccountExecutionCard', () => {
  beforeEach(() => {
    push.mockReset()
    vi.mocked(fetchCompanyWorkspace).mockReset()
    vi.mocked(fetchCompanyWorkspace).mockResolvedValue(workspace)
  })

  it('renders Account 360 commercial archive from company lifecycle sources', async () => {
    const wrapper = mount(AccountExecutionCard, {
      props: { companyId: 'company-1', contextLabel: '公司详情' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(fetchCompanyWorkspace).toHaveBeenCalledWith('company-1')
    expect(wrapper.text()).toContain('Account 360 商业档案')
    expect(wrapper.text()).toContain('Lead / 客户开发')
    expect(wrapper.text()).toContain('Opportunity / 项目机会')
    expect(wrapper.text()).toContain('Quote / 报价经验')
    expect(wrapper.text()).toContain('Order / Delivery')
    expect(wrapper.text()).toContain('Feedback / 售后反馈')
    expect(wrapper.text()).toContain('Win/Loss / Repeat')
    expect(wrapper.text()).toContain('完整度 6/6')
    expect(wrapper.text()).toContain('Resolve feedback, then create repeat-business motion.')
  })
})
