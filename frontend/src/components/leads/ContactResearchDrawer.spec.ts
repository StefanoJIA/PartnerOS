/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import ContactResearchDrawer from '@/components/leads/ContactResearchDrawer.vue'
import * as aDomain from '@/api/aDomain'

vi.mock('@/api/aDomain', () => ({
  postContactResearch: vi.fn().mockResolvedValue({
    lead_id: 'lead-1',
    interaction_id: 'ix-1',
    completeness: { score: 80 },
  }),
}))

const sampleRow = {
  leadId: 'lead-1',
  companyName: 'Transfer Enterprises',
  score: 42,
  status: 'needs_contact_research' as const,
  statusLabel: '需联系人调研',
  missingFields: ['contact_email_or_linkedin', 'website'],
  recommendedResearchAction: '补充邮箱或 LinkedIn 链接。',
  segments: [],
  nextAction: 'Research contact',
  lastTouch: '—',
}

describe('ContactResearchDrawer', () => {
  it('shows safety notice when open', async () => {
    const wrapper = mount(ContactResearchDrawer, {
      props: {
        visible: true,
        row: sampleRow,
        initial: null,
      },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('不会搜索 LinkedIn')
    expect(wrapper.text()).toContain('Transfer Enterprises')
  })

  it('shows missing fields', async () => {
    const wrapper = mount(ContactResearchDrawer, {
      props: { visible: true, row: sampleRow, initial: null },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('邮箱 / LinkedIn')
  })

  it('calls contact research API on save', async () => {
    const wrapper = mount(ContactResearchDrawer, {
      props: {
        visible: true,
        row: sampleRow,
        initial: {
          contactName: 'Jordan',
          contactEmail: 'jordan@transfer.example',
        },
      },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { form: Record<string, string>; save: () => Promise<void> }
    vm.form.contactName = 'Jordan Smith'
    vm.form.contactEmail = 'jordan@transfer.example'
    await vm.save()
    await flushPromises()
    expect(aDomain.postContactResearch).toHaveBeenCalledWith(
      'lead-1',
      expect.objectContaining({
        contact: expect.objectContaining({ email: 'jordan@transfer.example' }),
      }),
    )
  })

  it('empty save still calls API without breaking', async () => {
    const wrapper = mount(ContactResearchDrawer, {
      props: { visible: true, row: sampleRow, initial: null },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { save: () => Promise<void> }
    await vm.save()
    await flushPromises()
    expect(aDomain.postContactResearch).toHaveBeenCalled()
  })
})
