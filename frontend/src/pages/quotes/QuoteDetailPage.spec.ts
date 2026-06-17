/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import QuoteDetailPage from './QuoteDetailPage.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: 'q1' } }),
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('@/api/orders', () => ({
  fetchOrders: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  createOrderFromQuote: vi.fn(),
}))

vi.mock('@/api/quotes', () => ({
  SENT_CHANNELS: [{ value: 'email', label: 'Email (manual)' }],
  createQuoteLearning: vi.fn(),
  fetchQuote: vi.fn().mockResolvedValue({
    id: 'q1',
    quote_number: 'Q-2026-0001',
    status: 'ready_to_send',
    valid_until: '2026-06-13',
    derived_expired: false,
    payment_terms: 'Subject to confirmation',
    shipping_terms: 'Subject to confirmation',
    currency: 'USD',
    subtotal: '1000',
    grand_total: '1000',
    line_items: [],
    warnings: [],
    follow_up_date: null,
    sent_at: null,
    commercial_intelligence: {
      health: 'quote_learning_ready',
      score: 78,
      priority: 'P1',
      business_focus: 'HOSUN lifting systems',
      partner_focus: 'HOSUN',
      product_focus: ['lifting systems', 'heavy-duty supply'],
      version_count: 1,
      latest_outcome_status: 'won',
      follow_up_state: 'manual_follow_up',
      missing_inputs: [],
      captured_dimensions: ['load', 'stability'],
      dimension_review_needs: ['certification'],
      market_response_review_needed: true,
      quote_learning_impacts: [],
      readiness_impact: [],
      quote_playbook: {
        recommendation_type: 'internal_quote_playbook',
        status: 'ready',
        partner_focus: 'HOSUN',
        product_focus: ['lifting systems'],
        evidence_count: 2,
        won_count: 1,
        lost_count: 1,
        no_response_count: 0,
        deferred_count: 0,
        common_winning_factors: ['load'],
        common_loss_factors: ['certification'],
        quote_emphasis: ['load', 'stability'],
        avoid_or_validate_before_sending: ['certification', 'noise'],
        customer_safe_wording_needed: ['warranty'],
        customer_decision_factors: ['project demand'],
        product_factors: ['load', 'stability'],
        partner_factors: ['delivery support'],
        delivery_certification_service_factors: ['certification'],
        next_quote_guidance: 'Use load and stability proof before sending.',
        manual_only: true,
        customer_safe_boundary: 'Internal recommendation only.',
        safety: { external_message_sent: false, customer_notified: false, quote_status_changed: false, order_status_changed: false },
      },
      product_partner_playbook_refs: {
        recommendation_type: 'internal_product_partner_playbook_refs',
        partner_focus: 'HOSUN',
        product_focus: ['lifting systems'],
        product_playbooks: [
          {
            recommendation_type: 'internal_product_commercial_playbook',
            partner_focus: 'HOSUN',
            product_family: ['lifting systems', 'heavy-duty supply'],
            fit_status: 'order_validated',
            common_win_factors: ['load'],
            common_loss_factors: ['certification'],
            customer_decision_factors: ['project demand'],
            quote_emphasis_suggestions: ['load', 'stability'],
            risk_before_next_quote: ['certification', 'noise'],
            repeat_business_potential: 'strong_repeat_candidate',
            evidence_count: 6,
            next_commercial_action: 'Use product-family learning before this quote.',
            manual_only: true,
            customer_safe_boundary: 'Internal product commercial playbook only.',
            safety: { external_message_sent: false, customer_notified: false, quote_status_changed: false, order_status_changed: false },
          },
        ],
        partner_playbooks: [
          {
            recommendation_type: 'internal_partner_commercial_playbook',
            partner_name: 'HOSUN',
            product_coverage: ['lifting systems'],
            supported_product_families: ['lifting systems'],
            common_win_contribution: ['delivery support'],
            common_risk_factors: ['certification support'],
            quote_support_issues: ['customer-safe delivery wording'],
            delivery_certification_after_sales_issues: ['certification support'],
            pilot_suitability: 'selective_candidate',
            next_partner_action: 'Validate HOSUN certification support before quote send.',
            manual_only: true,
            customer_safe_boundary: 'Internal partner commercial playbook only.',
            safety: { external_message_sent: false, customer_notified: false, quote_status_changed: false, order_status_changed: false },
          },
        ],
        next_action: 'Use product-family learning before this quote.',
        manual_only: true,
        customer_safe_boundary: 'Internal playbook references only.',
        safety: { external_message_sent: false, customer_notified: false, quote_status_changed: false, order_status_changed: false },
      },
      next_best_action: 'Review playbook before manual quote send.',
      customer_safe_boundary: 'Internal only.',
      safety: { external_message_sent: false, customer_notified: false, quote_status_changed: false, order_status_changed: false },
    },
    partner_readiness: {
      health: 'partner_quote_gap',
      priority: 'P1',
      partners: [
        {
          partner_id: 'p1',
          partner_name: 'HOSUN',
          health: 'partner_quote_gap',
          priority: 'P1',
          readiness_score: 72,
          business_focus: '能力补齐',
          line_summary: { line_count: 1, requires_review_count: 1, product_categories: ['lifting systems'], sample_products: ['desk frame'] },
          dimension_baseline: ['load', 'noise', 'warranty'],
          missing_inputs: ['customer-safe delivery wording'],
          risk_signals: [],
          readiness_impact: ['quote send readiness'],
          next_best_action: '补齐 HOSUN 的客户可见交付表述。',
          capability_score: 78,
          customer_safe_boundary: 'internal only',
          safety: { external_message_sent: false, quote_status_changed: false, order_status_changed: false },
        },
      ],
      readiness_impact: ['quote send readiness'],
      missing_inputs: ['customer-safe delivery wording'],
      risk_signals: [],
      next_best_action: '补齐 partner 报价承接缺口。',
      customer_safe_boundary: '内部报价承接判断',
      safety: { external_message_sent: false, quote_status_changed: false, order_status_changed: false },
    },
  }),
  fetchQuotePdfExports: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  fetchQuoteLearning: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  fetchDeliveryLogs: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  fetchQuoteTimeline: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  fetchOrderReadiness: vi.fn().mockResolvedValue({
    quote_id: 'q1',
    quote_number: 'Q-2026-0001',
    readiness_status: 'needs_customer_confirmation',
    readiness_score: 80,
    blocking_items: [],
    warning_items: ['supplier_confirmation_needed'],
    checklist: [{ key: 'quote_sent', label: 'Quote has been sent', status: 'pass', details: '' }],
    order_input_contract: { customer: { company_name: 'Test Co' }, totals: { grand_total: '1000', currency: 'USD' }, line_items: [], source_quote: { quote_number: 'Q-2026-0001' } },
    recommended_next_action: 'Obtain customer confirmation',
    safety: { order_created: false, production_started: false, shipment_created: false, automatic_sending_enabled: false },
  }),
  exportQuotePdf: vi.fn(),
  fetchQuoteVersions: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  markQuoteReady: vi.fn(),
  markQuoteSent: vi.fn(),
  promoteQuoteLearningToMarketResponse: vi.fn(),
  quotePdfDownloadUrl: (qid: string, eid: string) => `/api/v1/quotes/${qid}/pdf-exports/${eid}/download`,
}))

describe('QuoteDetailPage', () => {
  it('renders delivery and timeline sections', async () => {
    const wrapper = mount(QuoteDetailPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Quote Delivery')
    expect(wrapper.text()).toContain('Partner 承接判断')
    expect(wrapper.text()).toContain('HOSUN')
    expect(wrapper.text()).toContain('Product / Partner Playbook Reference')
    expect(wrapper.text()).toContain('Use product-family learning before this quote.')
    expect(wrapper.text()).toContain('certification support')
    expect(wrapper.text()).toContain('Order Readiness')
    expect(wrapper.text()).toContain('Refresh Readiness')
    expect(wrapper.text()).toContain('does not create an order')
  })
})
