/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import PricingPreviewPage from '@/pages/quotes/PricingPreviewPage.vue'
import * as api from '@/api/quoteCatalog'

vi.mock('@/api/quoteCatalog', () => ({
  fetchCatalogProducts: vi.fn(),
  postPricingPreview: vi.fn(),
}))

describe('PricingPreviewPage', () => {
  beforeEach(() => {
    vi.mocked(api.fetchCatalogProducts).mockResolvedValue({
      items: [
        {
          id: 'p1',
          partner_id: 'x',
          internal_sku: 'HOSUN-FRAME-001',
          partner_product_code: null,
          product_name: 'Frame',
          product_category: 'lifting_frame',
          product_family: null,
          description_customer: null,
          status: 'active',
          attributes_json: null,
        },
      ],
      total: 1,
      page: 1,
      limit: 50,
    })
    vi.mocked(api.postPricingPreview).mockResolvedValue({
      product_id: 'p1',
      quantity: 100,
      incoterm: 'FOB',
      pricing_strategy: 'volume',
      currency: 'USD',
      source: 'price_tier',
      warnings: [],
      price_breakdown: { line_subtotal: '15800.00' },
      profit_breakdown: { estimated_margin: '25.00' },
      safety: {
        quote_created: false,
        automatic_sending_enabled: false,
        inventory_promised: false,
        certification_promised: false,
        lead_time_promised: false,
      },
    })
  })

  it('renders form and safety note', async () => {
    const wrapper = mount(PricingPreviewPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Pricing Preview')
    expect(wrapper.text()).toContain('Does not create quotes')
  })

  it('calls preview API', async () => {
    const wrapper = mount(PricingPreviewPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    await wrapper.find('button').trigger('click')
    await flushPromises()
    expect(api.postPricingPreview).toHaveBeenCalled()
    expect(wrapper.text()).toContain('15800.00')
  })
})
