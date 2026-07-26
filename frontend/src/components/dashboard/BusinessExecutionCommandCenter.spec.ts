/**
 * @vitest-environment happy-dom
 */
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { describe, expect, it, vi } from 'vitest'
import BusinessExecutionCommandCenter from './BusinessExecutionCommandCenter.vue'
import type { BusinessExecution } from '@/api/dashboard'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

const payload = {
  summary: {
    lifecycle_accounts: 1,
    active_opportunities: 1,
    quote_learning_items: 2,
    delivery_risks: 0,
    product_validation_items: 2,
    partner_investment_items: 2,
    commercial_intelligence_items: 12,
    executive_decisions: 1,
    status: 'READY_FOR_STAGING_HANDOFF',
    external_staging_state: 'WAITING_FOR_REAL_STAGING_EVIDENCE',
  },
  executive_decisions: [],
  account_lifecycle: [],
  lifecycle: [],
  opportunities: [],
  quotations: [],
  products: [],
  partners: [],
  delivery: [],
  safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
  commercial_intelligence: {
    executive_summary: {
      management_brief: [
        {
          key: 'who_to_follow',
          question: 'Who is most worth following today?',
          answer: 'HOSUN strategic account',
          evidence: 'Account 360 shows repeat motion and active quote learning.',
          recommended_action: 'Review feedback before repeat outreach.',
          source_assets: ['Account 360', 'Customer Value Intelligence'],
          path: '/companies/hosun',
          owner: 'account owner',
          partner_focus: 'HOSUN',
          product_focus: ['lifting systems', 'desk frames', 'lifting columns'],
          safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
        },
        {
          key: 'what_converts',
          question: 'What is most likely to convert?',
          answer: 'JOOBOO school desks/chairs project',
          evidence: 'Education furniture demand is tied to school procurement timing.',
          recommended_action: 'Use project furniture proof in the next quote review.',
          source_assets: ['Product-Market Fit Intelligence', 'Win/Loss Intelligence'],
          path: '/market-response',
          owner: 'product owner',
          partner_focus: 'JOOBOO',
          product_focus: ['education furniture', 'school desks/chairs'],
          safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
        },
        {
          key: 'future_revenue',
          question: 'Where will future revenue come from?',
          answer: 'Future partner pilot quote',
          evidence: 'Open opportunity and quote backlog are available.',
          recommended_action: 'Review revenue forecast before allocating partner capacity.',
          source_assets: ['Revenue Forecast Intelligence'],
          path: '/growth-operations',
          owner: 'sales owner',
          partner_focus: 'future partner',
          product_focus: ['project furniture'],
          safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
        },
      ],
      executive_actions: [
        {
          title: 'Legacy action should not be primary',
          reason: 'Fallback only.',
          next_action: 'Fallback action.',
          source_asset: 'legacy',
          path: '/',
        },
      ],
      commercial_snapshot: {
        total_weighted_revenue: 120000,
        forecast_quality_score: 70,
        at_risk_weighted_amount: 5000,
      },
      asset_map: [
        { asset: 'Win/Loss Intelligence', answers: 'why win/loss', items: 2, path: '/quotes' },
        { asset: 'Revenue Forecast Intelligence', answers: 'future revenue', items: 1, path: '/growth-operations' },
      ],
      safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
    },
    win_loss: [],
    customer_value: [],
    partner_performance: [],
    product_market_fit: [],
    revenue_forecast: {
      summary: {
        total_weighted_amount: 120000,
        at_risk_weighted_amount: 5000,
        forecast_quality_score: 70,
      },
      open_quote_amount: 80000,
      weighted_quote_amount: 64000,
      next_action: 'Review revenue forecast.',
      high_probability_projects: [],
      revenue_bucket_mix: [],
    },
    account_360: [],
  },
} as unknown as BusinessExecution

describe('BusinessExecutionCommandCenter', () => {
  it('renders management brief answers on the dashboard business chain', () => {
    const wrapper = mount(BusinessExecutionCommandCenter, {
      props: { data: payload },
      global: { plugins: [ElementPlus] },
    })

    expect(wrapper.text()).toContain('今天最值得跟进谁？')
    expect(wrapper.text()).toContain('HOSUN 重点客户')
    expect(wrapper.text()).toContain('先复核反馈，再进行复购触达。')
    expect(wrapper.text()).toContain('什么最可能转化？')
    expect(wrapper.text()).toContain('JOOBOO 学校桌椅项目')
    expect(wrapper.text()).toContain('未来收入可能来自哪里？')
    expect(wrapper.text()).toContain('未来 Partner 试点报价')
    expect(wrapper.text()).toContain('收入预测')
    expect(wrapper.text()).toContain('升降系统')
    expect(wrapper.text()).not.toContain('Legacy action should not be primary')
    expect(wrapper.text()).not.toContain('Who is most worth following today?')
  })
})
