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
  quotePdfDownloadUrl: (qid: string, eid: string) => `/api/v1/quotes/${qid}/pdf-exports/${eid}/download`,
}))

describe('QuoteDetailPage', () => {
  it('renders delivery and timeline sections', async () => {
    const wrapper = mount(QuoteDetailPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Quote Delivery')
    expect(wrapper.text()).toContain('Partner 承接判断')
    expect(wrapper.text()).toContain('HOSUN')
    expect(wrapper.text()).toContain('Order Readiness')
    expect(wrapper.text()).toContain('Refresh Readiness')
    expect(wrapper.text()).toContain('does not create an order')
  })
})
