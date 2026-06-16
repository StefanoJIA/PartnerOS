/**
 * @vitest-environment happy-dom
 */
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import CommercialIntelligencePage from './CommercialIntelligencePage.vue'
import {
  fetchAccount360Intelligence,
  fetchBusinessExecution,
  fetchProductMarketFitIntelligence,
  fetchWinLossIntelligenceDashboard,
  type Account360Intelligence,
  type BusinessExecution,
  type ProductMarketFitIntelligence,
  type WinLossIntelligenceDashboard,
} from '@/api/dashboard'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/api/dashboard', () => ({
  fetchAccount360Intelligence: vi.fn(),
  fetchBusinessExecution: vi.fn(),
  fetchProductMarketFitIntelligence: vi.fn(),
  fetchWinLossIntelligenceDashboard: vi.fn(),
}))

const payload = {
  summary: {
    lifecycle_accounts: 2,
    active_opportunities: 1,
    quote_learning_items: 1,
    delivery_risks: 0,
    product_validation_items: 2,
    partner_investment_items: 2,
    commercial_intelligence_items: 18,
    executive_decisions: 3,
    status: 'READY_FOR_STAGING_HANDOFF',
    external_staging_state: 'WAITING_FOR_REAL_STAGING_EVIDENCE',
  },
  account_lifecycle: [],
  lifecycle: [],
  opportunities: [],
  quotations: [],
  products: [],
  partners: [],
  delivery: [],
  executive_decisions: [],
  safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
  commercial_intelligence: {
    executive_summary: {
      management_questions: {
        who_to_follow_today: [
          {
            title: 'HOSUN demo account',
            reason: 'Account 360 shows repeat motion.',
            next_action: 'Review feedback before repeat outreach.',
            path: '/companies/demo',
            source_asset: 'account_360',
            priority: 'P1',
          },
        ],
        what_converts: [
          {
            title: 'HOSUN / lifting systems',
            reason: 'load and stability evidence support conversion.',
            next_action: 'Review PMF evidence.',
            path: '/market-response',
            source_asset: 'product_market_fit',
            priority: 'P1',
          },
        ],
        future_revenue_from: [{ title: 'JOOBOO education furniture pilot', probability: 80, weighted_amount: 80000, path: '/growth-operations' }],
        which_partner_to_invest: [{ title: 'JOOBOO', reason: 'Project furniture evidence is active.', path: '/partner-onboarding' }],
        why_we_win: [{ title: 'Won quote', reason: 'delivery consistency mattered.', path: '/quotes/q1' }],
        why_we_lose: [{ title: 'Lost quote', reason: 'certification evidence missing.', path: '/quotes/q2' }],
        what_is_commercially_healthy: [{ title: 'Growth account', reason: 'healthy revenue proxy without margin.', path: '/companies/c1' }],
      },
      commercial_snapshot: {
        total_weighted_revenue: 125000,
        forecast_quality_score: 72,
        at_risk_weighted_amount: 12000,
      },
      asset_map: [
        { asset: 'Win/Loss Intelligence', answers: '为什么赢 / 为什么输', items: 2, path: '/quotes' },
        { asset: 'Customer Value Intelligence', answers: '谁值得深跟', items: 1, path: '/companies' },
        { asset: 'Partner Performance Intelligence', answers: '哪个 Partner 值得投入', items: 1, path: '/partner-onboarding' },
        { asset: 'Product-Market Fit Intelligence', answers: '什么产品因素影响成交', items: 1, path: '/market-response' },
        { asset: 'Revenue Forecast Intelligence', answers: '未来收入来自哪里', items: 1, path: '/growth-operations' },
        { asset: 'Account 360', answers: '客户下一步商业动作', items: 1, path: '/growth-operations' },
      ],
      safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
    },
    account_360: [{ customer_name: 'HOSUN demo account', current_stage: 'After-Sales', priority: 'P1', next_action: 'Resolve feedback', path: '/companies/demo' }],
    product_market_fit: [{ partner_focus: 'HOSUN', product_focus: ['lifting systems'], fit_status: 'order_validated', commercial_question: 'Which factors convert?', next_action: 'Review load evidence', path: '/market-response' }],
    partner_performance: [{ partner_name: 'JOOBOO', investment_priority: 'P2', quote_support_count: 2, win_rate: 0.5, order_amount: 50000, next_action: 'Review allocation', path: '/partner-onboarding' }],
    win_loss: [{ customer: 'Won account', outcome: 'won', reason_category: 'delivery', commercial_lesson: 'Delivery consistency won.', next_quote_guidance: 'Use proof.', path: '/quotes/q1' }],
    customer_value: [{ customer_name: 'Growth account', value_tier: 'growth_account', priority: 'P1', historical_quote_amount: 100000, won_order_amount: 50000, weighted_pipeline_amount: 25000, next_action: 'Follow up', path: '/companies/c1' }],
    revenue_forecast: { high_probability_projects: [{ name: 'JOOBOO pilot', probability: 80, weighted_amount: 80000, path: '/growth-operations' }] },
  },
} as unknown as BusinessExecution

const winLossPayload = {
  summary: { total: 2, won: 1, lost: 1, open_or_unclear: 0, win_rate: 0.5, commercial_amount: 100000, opportunity_records: 1, quote_learning_records: 1 },
  items: [{ customer: 'HOSUN buyer', outcome: 'won', decision_factors: ['load', 'stability'] }],
  reason_clusters: [{ reason_category: 'delivery consistency', won: 1, lost: 0, next_quote_guidance: 'Reuse delivery proof.' }],
  partner_rollup: [{ partner_name: 'HOSUN', won: 1, lost: 1, sample_lessons: ['load matters'] }],
  product_rollup: [{ product_focus: 'lifting systems', won: 1, lost: 0, sample_lessons: ['noise proof needed'] }],
  decision_factor_rows: [{ factor: 'load', product_focus: 'lifting systems', next_quote_guidance: 'Use validated load range.' }],
  competitor_signals: [],
  management_questions: {},
  next_action: 'Review quote learning.',
  customer_safe_boundary: 'internal only',
  safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
} as unknown as WinLossIntelligenceDashboard

const pmfPayload = {
  summary: { product_line_count: 1, p1_product_line_count: 1, order_validated_count: 1, pilot_risk_count: 0, quote_learning_count: 1, feedback_signal_count: 0, order_amount: 50000 },
  items: [{ partner_focus: 'HOSUN', product_focus: ['lifting systems'], dimensions: ['load', 'stability'], buying_factors_ranked: [{ factor: 'stability', evidence_count: 3, wins: 1, losses: 0, feedback: 0 }] }],
  top_product_lines: [{ partner_focus: 'HOSUN', product_focus: ['lifting systems'], buying_factors_ranked: [{ factor: 'load', evidence_count: 4, wins: 1, losses: 0, feedback: 0 }] }],
  pilot_risk_product_lines: [],
  validated_buying_factors: [{ factor: 'load', partner_focus: 'HOSUN', evidence_count: 4, wins: 1, losses: 0, feedback: 0 }],
  management_questions: {},
  next_action: 'Review PMF.',
  safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
} as unknown as ProductMarketFitIntelligence

const accountPayload = {
  summary: {
    account_count: 1,
    p1_account_count: 1,
    strategic_account_count: 0,
    open_opportunity_count: 1,
    open_quote_count: 1,
    open_feedback_count: 0,
    weighted_pipeline_amount: 25000,
    won_order_amount: 50000,
    full_relationship_count: 1,
    quote_to_order_learning_count: 1,
    repeat_or_referral_motion_count: 1,
    reactivation_motion_count: 0,
  },
  items: [{ customer_name: 'HOSUN demo account', partner_focus: ['HOSUN'], product_focus: ['lifting systems'] }],
  recommended_accounts: [
    {
      customer_name: 'HOSUN demo account',
      priority: 'P1',
      current_stage: 'Repeat Business',
      path: '/companies/demo',
      next_commercial_motion: { next_action: 'Create repeat motion from won learning.' },
    },
  ],
  accounts_with_open_feedback: [],
  repeat_business_candidates: [],
  full_relationship_accounts: [],
  quote_to_order_learning_accounts: [],
  repeat_or_referral_accounts: [],
  reactivation_accounts: [],
  management_questions: {},
  next_action: 'Review accounts.',
  customer_safe_boundary: 'internal only',
  safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
} as unknown as Account360Intelligence

describe('CommercialIntelligencePage', () => {
  beforeEach(() => {
    push.mockReset()
    vi.mocked(fetchAccount360Intelligence).mockReset()
    vi.mocked(fetchBusinessExecution).mockReset()
    vi.mocked(fetchProductMarketFitIntelligence).mockReset()
    vi.mocked(fetchWinLossIntelligenceDashboard).mockReset()
    vi.mocked(fetchBusinessExecution).mockResolvedValue(payload)
    vi.mocked(fetchWinLossIntelligenceDashboard).mockResolvedValue(winLossPayload)
    vi.mocked(fetchProductMarketFitIntelligence).mockResolvedValue(pmfPayload)
    vi.mocked(fetchAccount360Intelligence).mockResolvedValue(accountPayload)
  })

  it('renders management questions and six commercial assets', async () => {
    const wrapper = mount(CommercialIntelligencePage, { global: { plugins: [ElementPlus] } })
    await flushPromises()

    expect(fetchBusinessExecution).toHaveBeenCalled()
    expect(fetchWinLossIntelligenceDashboard).toHaveBeenCalled()
    expect(fetchProductMarketFitIntelligence).toHaveBeenCalled()
    expect(fetchAccount360Intelligence).toHaveBeenCalled()
    expect(wrapper.text()).toContain('商业智能工作台')
    expect(wrapper.text()).toContain('谁最值得跟进')
    expect(wrapper.text()).toContain('什么最容易成交')
    expect(wrapper.text()).toContain('未来收入来自哪里')
    expect(wrapper.text()).toContain('Win/Loss Intelligence')
    expect(wrapper.text()).toContain('Product-Market Fit Intelligence')
    expect(wrapper.text()).toContain('Account 360')
    expect(wrapper.text()).toContain('HOSUN demo account')
    expect(wrapper.text()).toContain('JOOBOO')
    expect(wrapper.text()).toContain('商业经验库查询')
    expect(wrapper.text()).toContain('delivery consistency')
    expect(wrapper.text()).toContain('Use validated load range.')
    expect(wrapper.text()).toContain('Create repeat motion from won learning.')
  })

  it('keeps navigation as manual operator action', async () => {
    const wrapper = mount(CommercialIntelligencePage, { global: { plugins: [ElementPlus] } })
    await flushPromises()

    await wrapper.findAll('button').find((button) => button.text() === '返回行动看板')?.trigger('click')

    expect(push).toHaveBeenCalledWith('/')
  })
})
