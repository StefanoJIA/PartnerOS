/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import ProductFitCard from '@/components/leads/ProductFitCard.vue'
import * as aDomain from '@/api/aDomain'
import { PRODUCT_FIT_SAFETY } from '@/constants/productFit'

vi.mock('@/api/aDomain', () => ({
  fetchProductFit: vi.fn().mockResolvedValue({
    lead_id: 'lead-1',
    company_name: 'Ergo Sit Stand Workspace',
    recommended_product_focus: ['hosun_lifting_systems', 'adjustable_desk_frames'],
    project_opportunity_score: 78,
    opportunity_level: 'promising',
    project_type: 'dealer_supply',
    quote_readiness: 'almost_ready',
    sample_readiness: 'needs_specs',
    missing_quote_info: ['quantity_or_volume', 'project_timeline'],
    recommended_discovery_questions: [
      'Are you currently sourcing adjustable desk frames or lifting columns?',
      'Do you have target load capacity requirements?',
    ],
    recommended_next_product_action: 'Ask for quantity before preparing quote.',
    sales_angle: 'Position HOSUN lifting systems for Ergo Sit Stand Workspace.',
    warnings: ['Suggestions only.'],
  }),
}))

const mockFit = {
  lead_id: 'lead-1',
  company_name: 'Ergo Sit Stand Workspace',
  recommended_product_focus: ['hosun_lifting_systems', 'adjustable_desk_frames'],
  project_opportunity_score: 78,
  opportunity_level: 'promising',
  project_type: 'dealer_supply',
  quote_readiness: 'almost_ready',
  sample_readiness: 'needs_specs',
  missing_quote_info: ['quantity_or_volume', 'project_timeline'],
  recommended_discovery_questions: [
    'Are you currently sourcing adjustable desk frames or lifting columns?',
    'Do you have target load capacity requirements?',
  ],
  recommended_next_product_action: 'Ask for quantity before preparing quote.',
  sales_angle: 'Position HOSUN lifting systems for Ergo Sit Stand Workspace.',
  warnings: ['Suggestions only.'],
}

describe('ProductFitCard', () => {
  const writeText = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.mocked(aDomain.fetchProductFit).mockClear()
    writeText.mockClear()
    vi.stubGlobal('navigator', { clipboard: { writeText } })
  })

  it('renders product fit data', async () => {
    const wrapper = mount(ProductFitCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Product Fit & Project Opportunity')
    expect(wrapper.text()).toContain('78')
    expect(wrapper.text()).toContain('Promising')
    expect(wrapper.text()).toContain('HOSUN Lifting Systems')
  })

  it('renders product focus badges', async () => {
    const wrapper = mount(ProductFitCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Adjustable Desk Frames')
  })

  it('renders missing quote info', async () => {
    const wrapper = mount(ProductFitCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Quantity or volume')
    expect(wrapper.text()).toContain('Project timeline')
  })

  it('renders discovery questions', async () => {
    const wrapper = mount(ProductFitCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('adjustable desk frames or lifting columns')
  })

  it('shows safety note', async () => {
    const wrapper = mount(ProductFitCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain(PRODUCT_FIT_SAFETY)
  })

  it('copy questions works', async () => {
    const wrapper = mount(ProductFitCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { copyQuestions: () => Promise<void> }
    await vm.copyQuestions()
    expect(writeText).toHaveBeenCalledWith(
      mockFit.recommended_discovery_questions.join('\n\n'),
    )
  })

  it('shows error without white screen', async () => {
    vi.mocked(aDomain.fetchProductFit).mockRejectedValueOnce(new Error('Network Error'))
    const wrapper = mount(ProductFitCard, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('VITE_API_PROXY_TARGET')
  })
})
