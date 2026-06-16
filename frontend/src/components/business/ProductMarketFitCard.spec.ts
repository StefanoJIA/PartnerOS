/**
 * @vitest-environment happy-dom
 */
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ProductMarketFitCard from './ProductMarketFitCard.vue'
import { fetchProductMarketFitIntelligence, type ProductMarketFitIntelligence } from '@/api/dashboard'

vi.mock('@/api/dashboard', () => ({
  fetchProductMarketFitIntelligence: vi.fn(),
}))

const payload = {
  summary: {
    product_line_count: 1,
    p1_product_line_count: 1,
    order_validated_count: 1,
    pilot_risk_count: 0,
    quote_learning_count: 2,
    feedback_signal_count: 1,
    order_amount: 125000,
  },
  items: [
    {
      partner_focus: 'HOSUN',
      product_focus: ['lifting systems', 'desk frames', 'lifting columns', 'heavy-duty supply'],
      fit_status: 'order_validated',
      priority: 'P1',
      dimensions: ['load', 'stability', 'noise', 'certification'],
      evidence_counts: { opportunities: 3, quotes: 4, orders: 2, feedback: 1, quote_learning: 2 },
      commercial_value: { pipeline_amount: 80000, quote_amount: 150000, order_amount: 125000 },
      conversion_signal: { quote_to_order_rate: 0.5, win_loss_ratio: 0.75, validated_by_orders: true },
      buying_factors_ranked: [
        { factor: 'load', evidence_count: 5, wins: 2, losses: 0, feedback: 1, status: 'validated' },
        { factor: 'noise', evidence_count: 3, wins: 1, losses: 1, feedback: 1, status: 'needs evidence' },
      ],
      customer_objections: ['customer asked for quieter lifting column proof'],
      competitor_signals: ['local competitor claims shorter delivery'],
      project_experience: ['PO-100: confirmed; shipment present'],
      next_action: 'Review quote learning before customer-visible load and noise wording.',
      safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
    },
  ],
  top_product_lines: [],
  pilot_risk_product_lines: [],
  validated_buying_factors: [],
  management_questions: {},
  next_action: 'Review PMF.',
  safety: { external_message_sent: false, customer_forbidden_fields_exposed: false },
} as unknown as ProductMarketFitIntelligence

describe('ProductMarketFitCard', () => {
  beforeEach(() => {
    vi.mocked(fetchProductMarketFitIntelligence).mockReset()
    vi.mocked(fetchProductMarketFitIntelligence).mockResolvedValue(payload)
  })

  it('renders product-market fit evidence and buying factors for a product line', async () => {
    const wrapper = mount(ProductMarketFitCard, {
      props: {
        productName: 'HOSUN heavy-duty lifting column system',
        partnerFocus: 'HOSUN',
        productKeywords: ['lifting systems', 'desk frames', 'lifting columns', 'heavy-duty supply'],
        relatedOrderCount: 1,
      },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()

    expect(fetchProductMarketFitIntelligence).toHaveBeenCalledWith(120)
    expect(wrapper.text()).toContain('Product-Market Fit 智能')
    expect(wrapper.text()).toContain('P1 产品验证优先')
    expect(wrapper.text()).toContain('订单已验证')
    expect(wrapper.text()).toContain('报价转订单')
    expect(wrapper.text()).toContain('50%')
    expect(wrapper.text()).toContain('$125,000')
    expect(wrapper.text()).toContain('load')
    expect(wrapper.text()).toContain('noise')
    expect(wrapper.text()).toContain('客户可见表述需业务确认')
    expect(wrapper.text()).toContain('customer asked for quieter lifting column proof')
    expect(wrapper.text()).toContain('PO-100: confirmed; shipment present')
    expect(wrapper.text()).toContain('不暴露成本、利润、供应商私密备注')
  })
})
