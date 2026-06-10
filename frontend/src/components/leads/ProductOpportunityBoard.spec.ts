/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import ProductOpportunitySummary from '@/components/dashboard/ProductOpportunitySummary.vue'
import ProductOpportunityBoard from '@/components/leads/ProductOpportunityBoard.vue'
import * as productOpportunity from '@/api/productOpportunity'
import { PRODUCT_OPPORTUNITY_SAFETY } from '@/constants/productOpportunity'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('@/api/productOpportunity', () => ({
  fetchProductOpportunityBoard: vi.fn(),
}))

const mockBoard = {
  summary: {
    total: 2,
    high_opportunity: 1,
    promising: 1,
    quote_ready: 1,
    almost_ready: 1,
    almost_quote_ready: 1,
    sample_ready: 1,
    needs_specs: 1,
    lifting_system_fit: 1,
    project_supply_fit: 1,
    education_fit: 0,
    medical_fit: 0,
    oem_odm_fit: 0,
    oem_odm_potential: 0,
  },
  missing_info_summary: {
    quantity_or_volume: 2,
    project_timeline: 1,
  },
  rows: [
    {
      lead_id: 'lead-1',
      company_name: 'Ergo Sit Stand',
      project_opportunity_score: 82,
      opportunity_score: 82,
      opportunity_level: 'high_opportunity',
      project_type: 'dealer_supply',
      quote_readiness: 'almost_ready',
      sample_readiness: 'needs_specs',
      recommended_product_focus: ['hosun_lifting_systems', 'adjustable_desk_frames'],
      missing_quote_info: ['quantity_or_volume'],
      recommended_next_product_action: 'Ask for quantity.',
      next_action: 'Follow up',
      due_status: 'due_soon',
    },
  ],
  safety: {
    automatic_quote_creation: false,
    automatic_sending_enabled: false,
    price_promises_enabled: false,
    inventory_promises_enabled: false,
  },
  warnings: [],
  degraded: false,
}

describe('ProductOpportunitySummary', () => {
  beforeEach(() => {
    vi.mocked(productOpportunity.fetchProductOpportunityBoard).mockResolvedValue(mockBoard)
  })

  it('renders summary cards', async () => {
    const wrapper = mount(ProductOpportunitySummary, {
      global: { plugins: [ElementPlus], stubs: { SummaryCard: true } },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('产品机会摘要')
    expect(wrapper.text()).toContain(PRODUCT_OPPORTUNITY_SAFETY)
  })

  it('shows error without white screen', async () => {
    vi.mocked(productOpportunity.fetchProductOpportunityBoard).mockRejectedValueOnce(new Error('fail'))
    const wrapper = mount(ProductOpportunitySummary, {
      global: { plugins: [ElementPlus], stubs: { SummaryCard: true } },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('暂不可用')
  })
})

describe('ProductOpportunityBoard', () => {
  const writeText = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.mocked(productOpportunity.fetchProductOpportunityBoard).mockResolvedValue(mockBoard)
    writeText.mockClear()
    vi.stubGlobal('navigator', { clipboard: { writeText } })
  })

  it('renders rows and filters', async () => {
    const wrapper = mount(ProductOpportunityBoard, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Product Opportunity Board')
    expect(wrapper.text()).toContain('Ergo Sit Stand')
    expect(wrapper.text()).toContain('HOSUN Lifting Systems')
  })

  it('renders missing info summary', async () => {
    const wrapper = mount(ProductOpportunityBoard, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Most Common Missing Quote Info')
    expect(wrapper.text()).toContain('Quantity or volume')
  })

  it('copy common questions works', async () => {
    const wrapper = mount(ProductOpportunityBoard, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { copyCommonQuestions: () => Promise<void> }
    await vm.copyCommonQuestions()
    expect(writeText).toHaveBeenCalled()
  })

  it('shows safety note', async () => {
    const wrapper = mount(ProductOpportunityBoard, {
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain(PRODUCT_OPPORTUNITY_SAFETY)
  })
})
