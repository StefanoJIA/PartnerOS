"""Frontend API for D6.3 Customer Quotes."""

import { http } from '@/api/http'

export interface V1Envelope<T> {
  ok: boolean
  data: T
  meta?: { request_id?: string }
}

export interface QuoteSafety {
  quote_created: boolean
  automatic_sending_enabled: boolean
  inventory_promised: boolean
  certification_promised: boolean
  lead_time_promised: boolean
}

export interface QuoteLineItem {
  id: string
  line_number: number
  product_name: string
  quantity: number
  final_unit_price: string
  total_price: string
  pricing_source: string
  requires_review: boolean
  warnings: string[]
}

export interface QuoteSummary {
  id: string
  quote_number: string
  status: string
  quote_date: string
  valid_until: string
  grand_total: string
  currency: string
  bill_to_company: string | null
  derived_expired: boolean
  manual_sent: boolean
  safety: QuoteSafety
}

export interface QuoteDetail extends QuoteSummary {
  payment_terms: string | null
  shipping_terms: string | null
  subtotal: string
  adjustment_total: string
  tax_total: string
  line_items: QuoteLineItem[]
  adjustments: Array<{ id: string; type: string; label: string; amount: string }>
  versions_count: number
  warnings: string[]
  sent_at: string | null
  send_channel: string | null
}

export interface QuoteListData {
  items: QuoteSummary[]
  total: number
  page: number
  limit: number
}

export async function fetchQuotes(params?: { status?: string; search?: string }): Promise<QuoteListData> {
  const q = new URLSearchParams()
  if (params?.status) q.set('status', params.status)
  if (params?.search) q.set('search', params.search)
  const suffix = q.toString() ? `?${q}` : ''
  const { data } = await http.get<V1Envelope<QuoteListData>>(`/v1/quotes${suffix}`)
  return data.data
}

export async function fetchQuote(id: string): Promise<QuoteDetail> {
  const { data } = await http.get<V1Envelope<QuoteDetail>>(`/v1/quotes/${id}`)
  return data.data
}

export async function markQuoteReady(id: string): Promise<QuoteDetail> {
  const { data } = await http.post<V1Envelope<QuoteDetail>>(`/v1/quotes/${id}/mark-ready`)
  return data.data
}

export async function markQuoteSent(id: string, sendChannel?: string): Promise<QuoteDetail> {
  const { data } = await http.post<V1Envelope<QuoteDetail>>(`/v1/quotes/${id}/mark-sent`, {
    send_channel: sendChannel || 'manual',
  })
  return data.data
}
