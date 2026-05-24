/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import QuoteDetailPage from './QuoteDetailPage.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: 'q1' } }),
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
    expect(wrapper.text()).toContain('Order Readiness')
    expect(wrapper.text()).toContain('Refresh Readiness')
    expect(wrapper.text()).toContain('does not create an order')
  })
})
