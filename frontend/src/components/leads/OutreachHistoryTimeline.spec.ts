/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import OutreachHistoryTimeline from '@/components/leads/OutreachHistoryTimeline.vue'
import * as aDomain from '@/api/aDomain'
import { TIMELINE_EMPTY_MESSAGE, TIMELINE_SAFETY_NOTICE } from '@/constants/outreachTimeline'

vi.mock('@/api/aDomain', () => ({
  fetchLeadTimeline: vi.fn(),
}))

const emptyTimeline = {
  lead_id: 'lead-1',
  company_name: 'Demo Co',
  next_action: null,
  last_touchpoint_at: null,
  follow_up_hint: 'Needs first outreach',
  items: [],
  stats: {
    total_touchpoints: 0,
    manual_sent_count: 0,
    contact_research_count: 0,
    last_channel: null,
  },
}

const populatedTimeline = {
  lead_id: 'lead-1',
  company_name: 'Demo Co',
  next_action: 'Wait for reply',
  last_touchpoint_at: '2026-05-22T10:00:00+00:00',
  follow_up_hint: 'Waiting for reply',
  items: [
    {
      id: 'ix-1',
      timestamp: '2026-05-22T10:00:00+00:00',
      type: 'catalog_sent',
      channel: 'email',
      title: 'Email intro marked as sent',
      summary: '[manually_sent=true]',
      is_manual_send: true,
      is_contact_research: false,
    },
    {
      id: 'ix-2',
      timestamp: '2026-05-21T09:00:00+00:00',
      type: 'contact_research',
      channel: 'manual_research',
      title: 'Contact research updated',
      summary: '[manually_researched=true]',
      is_manual_send: false,
      is_contact_research: true,
    },
  ],
  stats: {
    total_touchpoints: 2,
    manual_sent_count: 1,
    contact_research_count: 1,
    last_channel: 'email',
  },
}

describe('OutreachHistoryTimeline', () => {
  beforeEach(() => {
    vi.mocked(aDomain.fetchLeadTimeline).mockReset()
  })

  it('renders empty state', async () => {
    vi.mocked(aDomain.fetchLeadTimeline).mockResolvedValue(emptyTimeline)
    const wrapper = mount(OutreachHistoryTimeline, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain(TIMELINE_EMPTY_MESSAGE)
  })

  it('renders timeline items', async () => {
    vi.mocked(aDomain.fetchLeadTimeline).mockResolvedValue(populatedTimeline)
    const wrapper = mount(OutreachHistoryTimeline, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Email intro marked as sent')
    expect(wrapper.text()).toContain('Contact research updated')
  })

  it('shows manual sent badge', async () => {
    vi.mocked(aDomain.fetchLeadTimeline).mockResolvedValue(populatedTimeline)
    const wrapper = mount(OutreachHistoryTimeline, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Manual send')
  })

  it('shows contact research badge', async () => {
    vi.mocked(aDomain.fetchLeadTimeline).mockResolvedValue(populatedTimeline)
    const wrapper = mount(OutreachHistoryTimeline, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Contact research')
  })

  it('shows safety note', async () => {
    vi.mocked(aDomain.fetchLeadTimeline).mockResolvedValue(emptyTimeline)
    const wrapper = mount(OutreachHistoryTimeline, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain(TIMELINE_SAFETY_NOTICE)
  })

  it('reloads when reload is called', async () => {
    vi.mocked(aDomain.fetchLeadTimeline).mockResolvedValue(emptyTimeline)
    const wrapper = mount(OutreachHistoryTimeline, {
      props: { leadId: 'lead-1' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(aDomain.fetchLeadTimeline).toHaveBeenCalledTimes(1)
    const vm = wrapper.vm as { reload: () => Promise<void> }
    await vm.reload()
    expect(aDomain.fetchLeadTimeline).toHaveBeenCalledTimes(2)
  })
})
