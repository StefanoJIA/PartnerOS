import { http } from '@/api/http'
import type { PreQuoteBrief } from '@/constants/preQuotePrep'

export type { PreQuoteBrief }

export async function fetchPreQuoteBrief(leadId: string) {
  const { data } = await http.get<PreQuoteBrief>(`/a-domain/leads/${leadId}/pre-quote-brief`)
  return data
}
