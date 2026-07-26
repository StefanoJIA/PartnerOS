import { http } from '@/api/http'
import type { QuoteInputContract } from '@/constants/quoteInputContract'

export type { QuoteInputContract }

export async function fetchQuoteInputContract(leadId: string) {
  const { data } = await http.get<QuoteInputContract>(`/a-domain/leads/${leadId}/quote-input-contract`)
  return data
}

export async function fetchProjectRequestQuoteInputContract(requestId: string) {
  const { data } = await http.get<{ quote_input_contract: QuoteInputContract }>(`/project-requests/${requestId}`)
  return data.quote_input_contract
}
