/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import QuoteInputContractCard from '@/components/leads/QuoteInputContractCard.vue'
import * as quoteInputContract from '@/api/quoteInputContract'
import { QUOTE_INPUT_CONTRACT_SAFETY } from '@/constants/quoteInputContract'

vi.mock('@/api/quoteInputContract', () => ({
  fetchQuoteInputContract: vi.fn(),
}))

const mockContract = {
  lead_id: 'lead-1',
  company_name: 'SWC Office Furniture',
  handoff_status: 'needs_customer_clarification',
  quote_module_readiness: 'needs_more_customer_info',
  recommended_partner_route: ['hosun_lifting_systems'],
  recommended_product_scope: ['adjustable_desk_frames'],
  quote_input_fields: {
    customer: {
      company_name: 'SWC Office Furniture',
      contact_name: 'Alex',
      contact_method_available: true,
    },
    product_intent: {
      product_focus: ['adjustable_desk_frames'],
      project_type: 'dealer_project',
      sample_readiness: 'needs_specs',
      quote_readiness: 'almost_ready',
    },
    known_requirements: {
      quantity_or_volume: null,
      product_type: null,
      frame_size_or_desktop_size: null,
      load_capacity_requirement: null,
      color_or_finish: null,
      delivery_location: null,
      project_timeline: null,
      certification_requirement: null,
      sample_quantity: null,
      oem_customization_requirement: null,
      component_category: null,
    },
    missing_requirements: ['quantity_or_volume', 'project_timeline'],
    recommended_questions: ['What quantity range should we consider?'],
    supplier_preparation_notes: ['Prepare adjustable desk frame overview.'],
  },
  copyable_json: '{"lead_id":"lead-1"}',
  copyable_handoff_summary: 'Quote Input Contract — SWC Office Furniture',
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

describe('QuoteInputContractCard', () => {
  const writeText = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.mocked(quoteInputContract.fetchQuoteInputContract).mockResolvedValue(mockContract)
    writeText.mockClear()
    vi.stubGlobal('navigator', { clipboard: { writeText } })
  })

  it('renders readiness and route badges', async () => {
    const wrapper = mount(QuoteInputContractCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Quote Input Contract')
    expect(wrapper.text()).toContain('Needs more customer information')
    expect(wrapper.text()).toContain('HOSUN lifting systems')
  })

  it('shows known requirements with Not confirmed for empty fields', async () => {
    const wrapper = mount(QuoteInputContractCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Not confirmed')
    expect(wrapper.text()).toContain('Quantity or volume')
  })

  it('shows safety note', async () => {
    const wrapper = mount(QuoteInputContractCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain(QUOTE_INPUT_CONTRACT_SAFETY)
  })

  it('copy summary works', async () => {
    const wrapper = mount(QuoteInputContractCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { copySummary: () => void }
    vm.copySummary()
    expect(writeText).toHaveBeenCalledWith(mockContract.copyable_handoff_summary)
  })

  it('error state does not white screen', async () => {
    vi.mocked(quoteInputContract.fetchQuoteInputContract).mockRejectedValueOnce(new Error('fail'))
    const wrapper = mount(QuoteInputContractCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('VITE_API_PROXY_TARGET')
  })
})
