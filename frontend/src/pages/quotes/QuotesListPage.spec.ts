/**
 * @vitest-environment happy-dom
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import QuotesListPage from './QuotesListPage.vue'
import { deleteQuote, fetchQuotes } from '@/api/quotes'

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
        status: 'internal_review',
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
  deleteQuote: vi.fn().mockResolvedValue({ archived: true, id: 'q1' }),
}))

describe('QuotesListPage', () => {
  beforeEach(() => {
    push.mockReset()
    vi.mocked(deleteQuote).mockClear()
    vi.mocked(fetchQuotes).mockClear()
  })

  it('renders safety note and quote list', async () => {
    const wrapper = mount(QuotesListPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('安全边界')
    expect(wrapper.text()).toContain('不会自动发送报价')
    expect(wrapper.text()).toContain('Q-2026-0001')
    expect(wrapper.text()).toContain('删除')
  })

  it('deletes an existing internal review quote and refreshes the list', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const wrapper = mount(QuotesListPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()

    await wrapper.findAll('button').find((button) => button.text() === '删除')?.trigger('click')
    await flushPromises()

    expect(confirmSpy).toHaveBeenCalledWith('删除报价 Q-2026-0001？此操作会归档该报价并从列表中移除。')
    expect(deleteQuote).toHaveBeenCalledWith('q1')
    expect(fetchQuotes).toHaveBeenCalledTimes(2)
    expect(push).not.toHaveBeenCalled()
  })

  it('keeps delete disabled for sent quotes', async () => {
    vi.mocked(fetchQuotes).mockResolvedValueOnce({
      items: [
        {
          id: 'q-sent',
          quote_number: 'Q-2026-0002',
          status: 'sent',
          quote_date: '2026-05-23',
          valid_until: '2026-06-13',
          grand_total: '1000.00',
          currency: 'USD',
          bill_to_company: 'Sent Co',
          derived_expired: false,
          manual_sent: true,
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
    })

    const wrapper = mount(QuotesListPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()

    const deleteButton = wrapper.findAll('button').find((button) => button.text() === '删除')
    expect(deleteButton?.attributes('disabled')).toBeDefined()
  })
})
