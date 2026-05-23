import { http } from '@/api/http'

export type LeadIntakePreviewRow = {
  row_number: number
  company_name: string
  contact_name: string
  website: string
  company_type: string
  source: string
  likely_segments: string[]
  priority_hint: string
  missing_fields: string[]
  duplicate_status: 'new' | 'possible_duplicate' | 'existing' | string
  recommended_next_action: string
  status: 'ok' | 'warn' | 'error' | string
  warnings: string[]
}

export type LeadIntakePreviewSummary = {
  total: number
  ok: number
  warnings: number
  errors: number
  duplicates: number
  ready_to_import: number
}

export type LeadIntakePreviewResponse = {
  rows: LeadIntakePreviewRow[]
  summary: LeadIntakePreviewSummary
  header_warnings: string[]
}

export type LeadIntakeApplyResponse = {
  created_companies: number
  skipped_duplicates: number
  created_contacts: number
  linked_leads: number
  warnings: string[]
}

export const LEAD_INTAKE_SAFETY_NOTICE =
  'intelliOffice only prepares human-reviewed lead records and drafts. It does not send messages or automate external platforms.'

export const LEAD_INTAKE_PRIVACY_NOTICE =
  'Uploaded CSV content is processed only inside the local intelliOffice backend. Do not commit private lead CSV files to git.'

export async function fetchLeadIntakeTemplate(): Promise<string> {
  const { data } = await http.get<string>('/a-domain/lead-intake/template', {
    responseType: 'text',
  })
  return data
}

export async function previewLeadIntake(csvText: string): Promise<LeadIntakePreviewResponse> {
  const { data } = await http.post<LeadIntakePreviewResponse>('/a-domain/lead-intake/preview', {
    csv_text: csvText,
  })
  return data
}

export async function applyLeadIntake(csvText: string): Promise<LeadIntakeApplyResponse> {
  const { data } = await http.post<LeadIntakeApplyResponse>('/a-domain/lead-intake/apply', {
    csv_text: csvText,
    confirm: true,
  })
  return data
}

export function downloadCsvBlob(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
