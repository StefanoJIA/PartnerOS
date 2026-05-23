/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/api/leadImport', () => ({
  LEAD_INTAKE_SAFETY_NOTICE:
    'intelliOffice only prepares human-reviewed lead records and drafts. It does not send messages or automate external platforms.',
  LEAD_INTAKE_PRIVACY_NOTICE:
    'Uploaded CSV content is processed only inside the local intelliOffice backend. Do not commit private lead CSV files to git.',
  fetchLeadIntakeTemplate: vi.fn(),
  previewLeadIntake: vi.fn(),
  applyLeadIntake: vi.fn(),
  downloadCsvBlob: vi.fn(),
}))

import LeadIntakePage from './LeadIntakePage.vue'
import {
  applyLeadIntake,
  previewLeadIntake,
  LEAD_INTAKE_SAFETY_NOTICE,
} from '@/api/leadImport'

const samplePreview = {
  rows: [
    {
      row_number: 1,
      company_name: 'Acme Co',
      contact_name: 'Alex',
      website: 'https://acme.example',
      company_type: 'Office Furniture Dealer',
      source: 'Trade show',
      likely_segments: ['lift_system_signal'],
      priority_hint: 'high',
      missing_fields: [],
      duplicate_status: 'new',
      recommended_next_action: 'Send catalog',
      status: 'ok',
      warnings: [],
    },
    {
      row_number: 2,
      company_name: '',
      contact_name: 'Missing',
      website: '',
      company_type: 'Other',
      source: '',
      likely_segments: [],
      priority_hint: 'low',
      missing_fields: ['company_name'],
      duplicate_status: 'new',
      recommended_next_action: 'Fix row',
      status: 'error',
      warnings: ['company_name is required'],
    },
    {
      row_number: 3,
      company_name: 'Dup Co',
      contact_name: 'Sam',
      website: '',
      company_type: 'Office Furniture Dealer',
      source: '',
      likely_segments: ['general_office_furniture_only'],
      priority_hint: 'medium',
      missing_fields: ['contact_email'],
      duplicate_status: 'existing',
      recommended_next_action: 'Research contact',
      status: 'warn',
      warnings: ['Duplicate: existing'],
    },
  ],
  summary: {
    total: 3,
    ok: 1,
    warnings: 1,
    errors: 1,
    duplicates: 1,
    ready_to_import: 2,
  },
  header_warnings: [],
}

function mountPage() {
  return mount(LeadIntakePage, {
    global: {
      plugins: [ElementPlus],
      stubs: { teleport: true },
    },
  })
}

describe('LeadIntakePage', () => {
  beforeEach(() => {
    vi.mocked(previewLeadIntake).mockReset()
    vi.mocked(applyLeadIntake).mockReset()
    push.mockReset()
  })

  it('renders title and safety notice', () => {
    const wrapper = mountPage()
    expect(wrapper.text()).toContain('Lead Intake')
    expect(wrapper.text()).toContain(LEAD_INTAKE_SAFETY_NOTICE)
  })

  it('preview CSV shows rows in summary', async () => {
    vi.mocked(previewLeadIntake).mockResolvedValueOnce(samplePreview)
    const wrapper = mountPage()
    await wrapper.find('textarea').setValue('company_name\nAcme,,,,,,,,,,,,,,,,\n')
    const previewBtn = wrapper.findAll('button').find((b) => b.text().includes('Preview'))
    expect(previewBtn).toBeTruthy()
    await previewBtn!.trigger('click')
    await flushPromises()
    expect(previewLeadIntake).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Acme Co')
    expect(wrapper.text()).toContain('Total rows')
  })

  it('missing company_name blocks import button', async () => {
    vi.mocked(previewLeadIntake).mockResolvedValueOnce(samplePreview)
    const wrapper = mountPage()
    await wrapper.find('textarea').setValue('csv')
    const previewBtn = wrapper.findAll('button').find((b) => b.text().includes('Preview'))
    await previewBtn!.trigger('click')
    await flushPromises()
    const confirmBtn = wrapper.findAll('button').find((b) => b.text().includes('Confirm Import'))
    expect(confirmBtn!.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Fix ERROR rows')
  })

  it('WARN rows allow confirm when no errors', async () => {
    const warnOnly = {
      ...samplePreview,
      rows: [samplePreview.rows[2]],
      summary: { total: 1, ok: 0, warnings: 1, errors: 0, duplicates: 1, ready_to_import: 1 },
    }
    vi.mocked(previewLeadIntake).mockResolvedValueOnce(warnOnly)
    const wrapper = mountPage()
    await wrapper.find('textarea').setValue('csv')
    await wrapper.findAll('button').find((b) => b.text().includes('Preview'))!.trigger('click')
    await flushPromises()
    const confirmBtn = wrapper.findAll('button').find((b) => b.text().includes('Confirm Import'))
    expect(confirmBtn!.attributes('disabled')).toBeUndefined()
  })

  it('shows duplicate status in preview table', async () => {
    vi.mocked(previewLeadIntake).mockResolvedValueOnce(samplePreview)
    const wrapper = mountPage()
    await wrapper.find('textarea').setValue('csv')
    await wrapper.findAll('button').find((b) => b.text().includes('Preview'))!.trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('existing')
  })
})
