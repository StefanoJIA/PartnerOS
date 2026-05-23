/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import PreQuotePrepCard from '@/components/leads/PreQuotePrepCard.vue'
import * as preQuotePrep from '@/api/preQuotePrep'
import { PRE_QUOTE_PREP_SAFETY } from '@/constants/preQuotePrep'

vi.mock('@/api/preQuotePrep', () => ({
  fetchPreQuoteBrief: vi.fn(),
}))

const mockBrief = {
  lead_id: 'lead-1',
  company_name: 'Ergo Sit Stand Workspace',
  quote_readiness: 'almost_ready',
  sample_readiness: 'needs_specs',
  recommended_product_focus: ['hosun_lifting_systems', 'adjustable_desk_frames'],
  project_type: 'dealer_supply',
  opportunity_score: 78,
  missing_quote_info: ['quantity_or_volume', 'project_timeline'],
  quote_preparation_checklist: [
    'Confirm product type.',
    'Confirm load capacity requirement.',
  ],
  sample_preparation_checklist: ['Confirm which model should be sampled.'],
  recommended_customer_questions: ['Are you sourcing adjustable desk frames?'],
  recommended_internal_next_steps: ['Send discovery questions.'],
  recommended_next_action: 'Ask for quantity before quote.',
  pre_quote_brief_text: 'Pre-Quote Preparation Brief — Ergo',
  sample_discussion_brief_text: 'Sample Discussion Brief — Ergo',
  warnings: ['No pricing commitments.'],
  safety: {
    quote_created: false,
    pricing_generated: false,
    inventory_promised: false,
    certification_promised: false,
    lead_time_promised: false,
    automatic_sending_enabled: false,
  },
}

describe('PreQuotePrepCard', () => {
  const writeText = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.mocked(preQuotePrep.fetchPreQuoteBrief).mockResolvedValue(mockBrief)
    writeText.mockClear()
    vi.stubGlobal('navigator', { clipboard: { writeText } })
  })

  it('renders readiness badges and checklists', async () => {
    const wrapper = mount(PreQuotePrepCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Pre-Quote & Sample Prep')
    expect(wrapper.text()).toContain('Almost Ready')
    expect(wrapper.text()).toContain('Confirm load capacity')
  })

  it('renders missing quote info', async () => {
    const wrapper = mount(PreQuotePrepCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Quantity or volume')
  })

  it('copy pre-quote brief works', async () => {
    const wrapper = mount(PreQuotePrepCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { copyPreQuoteBrief: () => Promise<void> }
    await vm.copyPreQuoteBrief()
    expect(writeText).toHaveBeenCalledWith(mockBrief.pre_quote_brief_text)
  })

  it('shows safety note', async () => {
    const wrapper = mount(PreQuotePrepCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain(PRE_QUOTE_PREP_SAFETY)
  })

  it('shows error without white screen', async () => {
    vi.mocked(preQuotePrep.fetchPreQuoteBrief).mockRejectedValueOnce(new Error('Network Error'))
    const wrapper = mount(PreQuotePrepCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('VITE_API_PROXY_TARGET')
  })
})
