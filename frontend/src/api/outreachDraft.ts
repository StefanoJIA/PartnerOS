import { http } from '@/api/http'

export type OutreachDraft = {
  channel: string
  language: string
  tone: string
  product_focus: string
  company_name: string
  segments: string[]
  linkedin_connect_note?: string | null
  email_subject?: string | null
  email_body?: string | null
  suggested_next_action: string
  suggested_touchpoint_type: string
}

export async function fetchOutreachDraft(params: {
  companyId: string
  channel: string
  language?: string
  tone?: string
  productFocus: string
}) {
  const { data } = await http.get<OutreachDraft>('/a-domain/outreach-draft', {
    params: {
      company_id: params.companyId,
      channel: params.channel,
      language: params.language || 'en',
      tone: params.tone || 'concise',
      product_focus: params.productFocus,
    },
  })
  return data
}
