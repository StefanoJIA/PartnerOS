/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import QuoteHandoffCard from '@/components/leads/QuoteHandoffCard.vue'
import * as quoteHandoff from '@/api/quoteHandoff'
import { QUOTE_HANDOFF_SAFETY } from '@/constants/quoteHandoff'

vi.mock('@/api/quoteHandoff', () => ({
  fetchQuoteHandoffBrief: vi.fn(),
}))

const mockBrief = {
  lead_id: 'lead-1',
  company_name: 'SWC Office Furniture',
  handoff_status: 'needs_customer_clarification',
  handoff_priority: 'medium',
  quote_readiness: 'almost_ready',
  sample_readiness: 'needs_specs',
  opportunity_score: 75,
  recommended_partner_route: ['hosun_lifting_systems'],
  recommended_product_scope: ['adjustable_desk_frames'],
  known_context: ['Office furniture dealer lead.'],
  missing_customer_info: ['quantity_or_volume'],
  supplier_preparation_notes: ['Prepare adjustable desk frame overview.'],
  customer_clarification_questions: ['What quantity range should we consider?'],
  recommended_next_step: 'Send clarification questions.',
  quote_handoff_brief_text: 'Quote Handoff Brief — SWC Office Furniture',
  supplier_notes_text: '- Prepare adjustable desk frame overview.',
  customer_questions_text: '1. What quantity range should we consider?',
  warnings: [],
  safety: {
    quote_created: false,
    pricing_generated: false,
    inventory_promised: false,
    certification_promised: false,
    lead_time_promised: false,
    automatic_sending_enabled: false,
  },
}

describe('QuoteHandoffCard', () => {
  const writeText = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.mocked(quoteHandoff.fetchQuoteHandoffBrief).mockResolvedValue(mockBrief)
    writeText.mockClear()
    vi.stubGlobal('navigator', { clipboard: { writeText } })
  })

  it('renders status badges and routes', async () => {
    const wrapper = mount(QuoteHandoffCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Soft Quote Handoff')
    expect(wrapper.text()).toContain('HOSUN lifting systems')
    expect(wrapper.text()).toContain('Needs customer clarification')
  })

  it('shows safety note', async () => {
    const wrapper = mount(QuoteHandoffCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain(QUOTE_HANDOFF_SAFETY)
  })

  it('copy handoff brief works', async () => {
    const wrapper = mount(QuoteHandoffCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { copyHandoffBrief: () => void }
    vm.copyHandoffBrief()
    expect(writeText).toHaveBeenCalledWith(mockBrief.quote_handoff_brief_text)
  })

  it('error state does not white screen', async () => {
    vi.mocked(quoteHandoff.fetchQuoteHandoffBrief).mockRejectedValueOnce(new Error('fail'))
    const wrapper = mount(QuoteHandoffCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('VITE_API_PROXY_TARGET')
  })
})
