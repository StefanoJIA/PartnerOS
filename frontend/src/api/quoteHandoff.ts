import { http } from '@/api/http'
import type { QuoteHandoffBrief } from '@/constants/quoteHandoff'

export type { QuoteHandoffBrief }

export async function fetchQuoteHandoffBrief(leadId: string) {
  const { data } = await http.get<QuoteHandoffBrief>(`/a-domain/leads/${leadId}/quote-handoff-brief`)
  return data
}
