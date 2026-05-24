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
  fetchQuote: vi.fn().mockResolvedValue({
    id: 'q1',
    quote_number: 'Q-2026-0001',
    status: 'ready_to_send',
    valid_until: '2026-06-13',
    payment_terms: 'Subject to confirmation',
    shipping_terms: 'Subject to confirmation',
    currency: 'USD',
    subtotal: '1000',
    grand_total: '1000',
    line_items: [],
    warnings: [],
  }),
  fetchQuotePdfExports: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  exportQuotePdf: vi.fn().mockResolvedValue({
    export_id: 'e1',
    file_name: 'Quote_Q-2026-0001_v1_20260524.pdf',
    file_size_bytes: 1234,
    download_url: '/api/v1/quotes/q1/pdf-exports/e1/download',
    safety: {
      automatic_sending_enabled: false,
      inventory_promised: false,
      certification_promised: false,
      lead_time_promised: false,
    },
  }),
  markQuoteReady: vi.fn(),
  markQuoteSent: vi.fn(),
  quotePdfDownloadUrl: (qid: string, eid: string) => `/api/v1/quotes/${qid}/pdf-exports/${eid}/download`,
}))

describe('QuoteDetailPage', () => {
  it('renders PDF export section', async () => {
    const wrapper = mount(QuoteDetailPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Quote PDF Exports')
    expect(wrapper.text()).toContain('Export Customer PDF')
    expect(wrapper.text()).toContain('Exporting a PDF does not send the quote')
  })
})
