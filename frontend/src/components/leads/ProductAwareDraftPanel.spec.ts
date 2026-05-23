/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import ProductAwareDraftPanel from '@/components/leads/ProductAwareDraftPanel.vue'
import * as productAwareDraft from '@/api/productAwareDraft'
import { PRODUCT_AWARE_DRAFT_SAFETY } from '@/constants/productAwareDraft'

vi.mock('@/api/productAwareDraft', () => ({
  fetchProductAwareDraft: vi.fn(),
}))

const mockDraft = {
  lead_id: 'lead-1',
  company_name: 'Ergo Sit Stand Workspace',
  channel: 'email_intro',
  draft_purpose: 'product_discovery',
  tone: 'warm',
  language: 'en',
  subject: 'intelliOffice — adjustable desk frame / lifting system discussion',
  body: 'Hi Alex,\n\nLifting systems discussion without pricing promises.',
  linkedin_note: null,
  questions: ['Are you sourcing adjustable desk frames?'],
  recommended_next_action: 'Send manually after review.',
  suggested_follow_up_days: 5,
  source_context: {
    product_focus: ['hosun_lifting_systems'],
    quote_readiness: 'almost_ready',
    sample_readiness: 'needs_specs',
    missing_quote_info: [],
  },
  safety: {
    quote_created: false,
    pricing_generated: false,
    inventory_promised: false,
    certification_promised: false,
    lead_time_promised: false,
    automatic_sending_enabled: false,
  },
  warnings: ['Human review required.'],
}

describe('ProductAwareDraftPanel', () => {
  const writeText = vi.fn().mockResolvedValue(undefined)

  beforeEach(() => {
    vi.mocked(productAwareDraft.fetchProductAwareDraft).mockResolvedValue(mockDraft)
    writeText.mockClear()
    vi.stubGlobal('navigator', { clipboard: { writeText } })
  })

  it('renders and generates draft', async () => {
    const wrapper = mount(ProductAwareDraftPanel, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { generate: () => Promise<void> }
    await vm.generate()
    await flushPromises()
    expect(productAwareDraft.fetchProductAwareDraft).toHaveBeenCalled()
    expect(wrapper.text()).toContain('adjustable desk frame')
  })

  it('shows safety note', async () => {
    const wrapper = mount(ProductAwareDraftPanel, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain(PRODUCT_AWARE_DRAFT_SAFETY)
  })

  it('copy draft works', async () => {
    const wrapper = mount(ProductAwareDraftPanel, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { generate: () => Promise<void>; copyDraft: () => void }
    await vm.generate()
    await flushPromises()
    vm.copyDraft()
    expect(writeText).toHaveBeenCalled()
  })

  it('error state does not white screen', async () => {
    vi.mocked(productAwareDraft.fetchProductAwareDraft).mockRejectedValueOnce(new Error('fail'))
    const wrapper = mount(ProductAwareDraftPanel, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { generate: () => Promise<void> }
    await vm.generate()
    await flushPromises()
    expect(wrapper.text()).toContain('VITE_API_PROXY_TARGET')
  })
})
