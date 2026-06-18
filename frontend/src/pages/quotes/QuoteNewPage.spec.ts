/**
 * @vitest-environment happy-dom
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import QuoteNewPage from '@/pages/quotes/QuoteNewPage.vue'
import * as catalogApi from '@/api/quoteCatalog'
import { http } from '@/api/http'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/api/quoteCatalog', () => ({
  fetchCatalogProducts: vi.fn(),
  postPricingPreview: vi.fn(),
}))

vi.mock('@/api/http', () => ({
  http: {
    post: vi.fn(),
  },
}))

describe('QuoteNewPage', () => {
  beforeEach(() => {
    push.mockReset()
    vi.mocked(catalogApi.fetchCatalogProducts).mockResolvedValue({
      items: [
        {
          id: 'p1',
          partner_id: 'partner-1',
          internal_sku: 'DF0402',
          partner_product_code: null,
          product_name: 'Chair',
          product_category: 'education_furniture',
          product_family: 'school desks/chairs',
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
    vi.mocked(catalogApi.postPricingPreview).mockResolvedValue({
      product_id: 'p1',
      quantity: 50,
      incoterm: 'DDP',
      pricing_strategy: 'volume',
      currency: 'USD',
      source: 'price_tier',
      warnings: [],
      cost_breakdown: { fob_cost_usd: '22.00', ddp_cost_usd: '62.00' },
      price_breakdown: { final_unit_price_after_discount: '79.43', line_subtotal: '3971.50' },
      profit_breakdown: {},
      quote_model: {
        workflow: [],
        product: { id: 'p1', name: 'Chair', category: 'education_furniture', family: 'school desks/chairs' },
        inputs: {},
        fx_stage: {},
        cost_stage: {},
        logistics_stage: {},
        pricing_stage: {},
        discount_stage: {},
        final_quote_stage: {
          interval_quote_table: [
            {
              min_qty: 1,
              max_qty: 49,
              quantity_label: '1-49',
              currency: 'USD',
              fob_unit_price: null,
              ddp_unit_price: '82.74',
              incoterms_available: ['DDP'],
            },
            {
              min_qty: 50,
              max_qty: 99,
              quantity_label: '50-99',
              currency: 'USD',
              fob_unit_price: '25.28',
              ddp_unit_price: '79.43',
              incoterms_available: ['FOB', 'DDP'],
            },
          ],
        },
        profit_stage: {},
        customer_safe_boundary: 'customer-safe interval table only',
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
    vi.mocked(http.post).mockResolvedValue({ data: { ok: true, data: { id: 'q1' } } })
  })

  it('builds an editable English quote sheet and submits interval rows', async () => {
    const wrapper = mount(QuoteNewPage, { global: { plugins: [ElementPlus] } })
    await flushPromises()

    expect(wrapper.text()).toContain('新建报价单')
    expect(wrapper.text()).toContain('BILL TO')
    expect(wrapper.text()).toContain('EXW Unit Price')

    const addButton = wrapper.findAll('button').find((button) => button.text().includes('添加产品'))
    expect(addButton).toBeTruthy()
    await addButton!.trigger('click')
    await flushPromises()
    await flushPromises()
    await vi.waitFor(() => {
      const vm = wrapper.vm as unknown as {
        blocks: Array<{ loading: boolean; rows: unknown[] }>
      }
      expect(vm.blocks[0]?.loading).toBe(false)
      expect(vm.blocks[0]?.rows.length).toBe(2)
    })
    await wrapper.vm.$nextTick()

    expect(catalogApi.postPricingPreview).toHaveBeenCalledWith({
      product_id: 'p1',
      quantity: 50,
      incoterm: 'DDP',
      pricing_strategy: 'volume',
    })
    expect(wrapper.text()).toContain('DF0402')
    expect(wrapper.text()).toContain('1 ~ 49')
    expect(wrapper.text()).toContain('50 ~ 99')

    const vm = wrapper.vm as unknown as {
      blocks: Array<{ rows: Array<{ ddp_unit_price: string }> }>
    }
    vm.blocks[0].rows[1].ddp_unit_price = '78.50'

    const saveButton = wrapper.findAll('button').find((button) => button.text().includes('保存报价'))
    expect(saveButton).toBeTruthy()
    await saveButton!.trigger('click')
    await flushPromises()

    expect(http.post).toHaveBeenCalledWith(
      '/v1/quotes',
      expect.objectContaining({
        line_items: [
          expect.objectContaining({
            product_id: 'p1',
            quantity: 50,
            incoterm: 'DDP',
            manual_interval_quote_table: [
              expect.objectContaining({ quantity_label: '1-49', ddp_unit_price: '82.74' }),
              expect.objectContaining({ quantity_label: '50-99', ddp_unit_price: '78.50' }),
            ],
          }),
        ],
      }),
    )
    expect(push).toHaveBeenCalledWith({ name: 'quote-detail', params: { id: 'q1' } })
  })
})
