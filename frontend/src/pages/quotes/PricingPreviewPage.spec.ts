/**
 * @vitest-environment happy-dom
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
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
          image_url: null,
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
      cost_breakdown: {
        unit_material_cost_rmb: '720.00',
        unit_material_cost_after_domestic_profit_rmb: '784.80',
        unit_material_cost_usd: '100.00',
        fob_cost_usd: '109.00',
        ddp_cost_usd: '158.00',
      },
      price_breakdown: {
        final_unit_price_after_discount: '158.00',
        line_subtotal: '15800.00',
      },
      profit_breakdown: { estimated_margin: '25.00' },
      quote_model: {
        workflow: [
          { step: 'cost', workbook_sheet: 'cost', status: 'calculated' },
          { step: 'customer_quote', workbook_sheet: 'Quote', status: 'customer_safe_output' },
        ],
        product: { id: 'p1', name: 'Frame', category: 'lifting_frame', family: null },
        inputs: {},
        fx_stage: { rate: '7.2', source: 'demo' },
        cost_stage: { material_cost_rmb: '720.00', fob_cost_usd: '109.00', ddp_cost_usd: '158.00' },
        logistics_stage: { freight_cost_usd: '49.00' },
        pricing_stage: { source: 'price_tier' },
        discount_stage: { discount_amount: '0.00', final_unit_price_after_discount: '158.00' },
        final_quote_stage: {
          unit_price: '158.00',
          line_subtotal: '15800.00',
          interval_quote_table: [
            {
              min_qty: 1,
              max_qty: 49,
              quantity_label: '1-49',
              currency: 'USD',
              fob_unit_price: null,
              ddp_unit_price: '180.00',
              incoterms_available: ['DDP'],
            },
            {
              min_qty: 50,
              max_qty: 99,
              quantity_label: '50-99',
              currency: 'USD',
              fob_unit_price: '120.00',
              ddp_unit_price: '158.00',
              incoterms_available: ['FOB', 'DDP'],
            },
          ],
        },
        profit_stage: { estimated_margin: '25.00' },
        customer_safe_boundary: 'PDF/customer output may show final price only.',
        warnings: [],
        safety: {
          quote_created: false,
          automatic_sending_enabled: false,
          inventory_promised: false,
          certification_promised: false,
          lead_time_promised: false,
        },
      },
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
    expect(wrapper.text()).toContain('报价流程预览')
    expect(wrapper.text()).toContain('不会创建报价')
  })

  it('calls preview API and renders product interval quote table', async () => {
    const wrapper = mount(PricingPreviewPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    await wrapper.find('button').trigger('click')
    await flushPromises()
    expect(api.postPricingPreview).toHaveBeenCalled()
    expect(wrapper.text()).toContain('15800.00')
    expect(wrapper.text()).toContain('价目表区间报价')
    expect(wrapper.text()).toContain('1-49')
    expect(wrapper.text()).toContain('50-99')
  })
})
