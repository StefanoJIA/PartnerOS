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
  fetchQuoteVersions: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  exportQuotePdf: vi.fn(),
  markQuoteReady: vi.fn(),
  markQuoteSent: vi.fn(),
  quotePdfDownloadUrl: (qid: string, eid: string) => `/api/v1/quotes/${qid}/pdf-exports/${eid}/download`,
}))

describe('QuoteDetailPage', () => {
  it('renders delivery and timeline sections', async () => {
    const wrapper = mount(QuoteDetailPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Quote Delivery')
    expect(wrapper.text()).toContain('Quote Timeline')
    expect(wrapper.text()).toContain('Mark as Sent (manual)')
    expect(wrapper.text()).toContain('Recording a sent quote only documents a manual external action')
  })
})
