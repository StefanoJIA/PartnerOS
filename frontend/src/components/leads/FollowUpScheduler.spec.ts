/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import FollowUpScheduler from '@/components/leads/FollowUpScheduler.vue'
import * as aDomain from '@/api/aDomain'
import { FOLLOW_UP_SCHEDULER_SAFETY, quickFollowUpDates } from '@/constants/followUpScheduling'

vi.mock('@/api/aDomain', () => ({
  patchLeadFollowUp: vi.fn().mockResolvedValue({ lead_id: 'lead-1' }),
}))

describe('FollowUpScheduler', () => {
  beforeEach(() => {
    vi.mocked(aDomain.patchLeadFollowUp).mockClear()
  })

  it('renders safety note', async () => {
    const wrapper = mount(FollowUpScheduler, {
      props: { leadId: 'lead-1', initialDate: null, initialNextAction: null },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain(FOLLOW_UP_SCHEDULER_SAFETY)
  })

  it('quick buttons compute dates', async () => {
    const wrapper = mount(FollowUpScheduler, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as { applyQuick: (k: 'in5Days') => void; form: { nextFollowUpDate: string } }
    vm.applyQuick('in5Days')
    expect(vm.form.nextFollowUpDate).toBe(quickFollowUpDates().in5Days)
  })

  it('save calls API', async () => {
    const wrapper = mount(FollowUpScheduler, {
      props: { leadId: 'lead-1', initialNextAction: 'Wait for reply' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const vm = wrapper.vm as {
      form: { nextFollowUpDate: string; nextAction: string }
      save: () => Promise<void>
    }
    vm.form.nextFollowUpDate = quickFollowUpDates().in5Days
    vm.form.nextAction = 'Follow up in 5 days'
    await vm.save()
    await flushPromises()
    expect(aDomain.patchLeadFollowUp).toHaveBeenCalledWith(
      'lead-1',
      expect.objectContaining({
        next_follow_up_date: quickFollowUpDates().in5Days,
        next_action: 'Follow up in 5 days',
      }),
    )
  })
})
