/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import QuotesListPage from './QuotesListPage.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/api/quotes', () => ({
  fetchQuotes: vi.fn().mockResolvedValue({
    items: [
      {
        id: 'q1',
        quote_number: 'Q-2026-0001',
        status: 'ready_to_send',
        quote_date: '2026-05-23',
        valid_until: '2026-06-13',
        grand_total: '1000.00',
        currency: 'USD',
        bill_to_company: 'Test Co',
        derived_expired: false,
        manual_sent: false,
        safety: {
          quote_created: true,
          automatic_sending_enabled: false,
          inventory_promised: false,
          certification_promised: false,
          lead_time_promised: false,
        },
      },
    ],
    total: 1,
    page: 1,
    limit: 50,
  }),
}))

describe('QuotesListPage', () => {
  it('renders safety note and quote list', async () => {
    const wrapper = mount(QuotesListPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Safety')
    expect(wrapper.text()).toContain('does not send quotes automatically')
    expect(wrapper.text()).toContain('Q-2026-0001')
  })
})
