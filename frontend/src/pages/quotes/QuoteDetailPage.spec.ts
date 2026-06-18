/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
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
    quote_date: '2026-06-18',
    valid_until: '2026-07-09',
    derived_expired: false,
    payment_terms: 'Subject to confirmation',
    shipping_terms: 'FOB / DDP',
    currency: 'USD',
    subtotal: '1000',
    adjustment_total: '0',
    tax_total: '0',
    grand_total: '1000',
    bill_to_company: 'OCI Office Concepts Inc.',
    warnings: [],
    follow_up_date: null,
    sent_at: null,
    send_channel: null,
    manual_sent: false,
    safety: {
      quote_created: true,
      automatic_sending_enabled: false,
      inventory_promised: false,
      certification_promised: false,
      lead_time_promised: false,
    },
    versions_count: 1,
    adjustments: [],
    line_items: [
      {
        id: 'li1',
        line_number: 1,
        product_name: 'HOSUN Heavy-duty Lifting System',
        quantity: 50,
        final_unit_price: '128.00',
        total_price: '6400.00',
        pricing_source: 'interval pricing model',
        requires_review: false,
        warnings: [],
        interval_quote_table: [
          {
            min_qty: 1,
            max_qty: 49,
            quantity_label: '1-49',
            currency: 'USD',
            fob_unit_price: '138.00',
            ddp_unit_price: '168.00',
            incoterms_available: ['FOB', 'DDP'],
            customer_visible: true,
          },
          {
            min_qty: 50,
            max_qty: 99,
            quantity_label: '50-99',
            currency: 'USD',
            fob_unit_price: '128.00',
            ddp_unit_price: '156.00',
            incoterms_available: ['FOB', 'DDP'],
            customer_visible: true,
          },
          {
            min_qty: 500,
            max_qty: null,
            quantity_label: '>=500',
            currency: 'USD',
            fob_unit_price: '109.00',
            ddp_unit_price: '132.00',
            incoterms_available: ['FOB', 'DDP'],
            customer_visible: true,
          },
        ],
      },
    ],
    latest_learning: null,
  }),
  fetchQuotePdfExports: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  fetchQuoteLearning: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  fetchDeliveryLogs: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  fetchQuoteTimeline: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  fetchQuoteVersions: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  fetchOrderReadiness: vi.fn().mockResolvedValue({
    quote_id: 'q1',
    quote_number: 'Q-2026-0001',
    readiness_status: 'needs_customer_confirmation',
    readiness_score: 80,
    blocking_items: [],
    warning_items: ['supplier_confirmation_needed'],
    checklist: [{ key: 'quote_sent', label: 'Quote has been sent', status: 'pass', details: '' }],
    order_input_contract: {
      customer: { company_name: 'OCI Office Concepts Inc.' },
      totals: { grand_total: '1000', currency: 'USD' },
      line_items: [],
      source_quote: { quote_number: 'Q-2026-0001' },
    },
    recommended_next_action: 'Obtain customer confirmation',
    safety: {
      order_created: false,
      production_started: false,
      shipment_created: false,
      automatic_sending_enabled: false,
    },
  }),
  exportQuotePdf: vi.fn(),
  markQuoteReady: vi.fn(),
  markQuoteSent: vi.fn(),
  promoteQuoteLearningToMarketResponse: vi.fn(),
  quotePdfDownloadUrl: (qid: string, eid: string) => `/api/v1/quotes/${qid}/pdf-exports/${eid}/download`,
}))

describe('QuoteDetailPage', () => {
  it('renders quote-focused detail sections in Chinese', async () => {
    const wrapper = mount(QuoteDetailPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()

    const text = wrapper.text()
    expect(text).toContain('报价详情 Q-2026-0001')
    expect(text).toContain('报价基本信息')
    expect(text).toContain('客户报价区间表')
    expect(text).toContain('每个产品完整展示所有数量区间')
    expect(text).toContain('HOSUN Heavy-duty Lifting System')
    expect(text).toContain('1-49')
    expect(text).toContain('50-99')
    expect(text).toContain('>=500')
    expect(text).toContain('报价产品明细')
    expect(text).toContain('客户 PDF')
    expect(text).toContain('人工发送记录')
    expect(text).toContain('转订单准备')
    expect(text).toContain('刷新检查')
    expect(text).toContain('内部记录：客户反馈 / 赢输原因 / Market Response')
    expect(text).not.toContain('Product / Partner Playbook Reference')
    expect(text).not.toContain('Quote Delivery')
  })
})
