"""Frontend API for D6.3+ Customer Quotes."""

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

export interface DeliverySafety {
  automatic_sending_enabled: boolean
  email_sent_by_system: boolean
  linkedin_sent_by_system: boolean
  attachment_sent_by_system: boolean
  order_created: boolean
  inventory_promised?: boolean
  certification_promised?: boolean
  lead_time_promised?: boolean
}

export interface DeliveryLog {
  id: string
  quote_id: string
  quote_version_id: string | null
  pdf_export_id: string | null
  sent_channel: string
  sent_to_name: string | null
  sent_to_email: string | null
  sent_to_company: string | null
  sent_at: string | null
  manual_sent: boolean
  follow_up_date: string | null
  note: string | null
  status: string
}

export interface MarkSentPayload {
  quote_version_id?: string
  pdf_export_id?: string
  sent_channel?: string
  send_channel?: string
  sent_to_name?: string
  sent_to_email?: string
  sent_to_company?: string
  sent_at?: string
  follow_up_date?: string
  note?: string
}

export interface MarkSentResult {
  quote_id: string
  status: string
  delivery_log: DeliveryLog
  follow_up_date?: string | null
  warnings?: string[]
  safety: DeliverySafety
}

export interface TimelineItem {
  type: string
  title: string
  timestamp: string | null
  actor?: string
  channel?: string
  meta?: Record<string, unknown>
}

export interface PdfExportSafety {
  automatic_sending_enabled: boolean
  inventory_promised: boolean
  certification_promised: boolean
  lead_time_promised: boolean
  order_created?: boolean
}

export interface PdfExportRecord {
  export_id: string
  quote_id: string
  quote_version_id: string | null
  export_type: string
  file_name: string
  file_size_bytes: number | null
  content_type: string
  status: string
  exported_at: string | null
  download_url: string
}

export interface PdfExportResult {
  export_id: string
  file_name: string
  content_type: string
  file_size_bytes: number
  download_url: string
  safety: PdfExportSafety
}

export interface PdfExportListData {
  items: PdfExportRecord[]
  total: number
}

export interface QuoteVersionSummary {
  id: string
  version_number: number
  version_label: string | null
  version_type: string
  created_at: string | null
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
  follow_up_date: string | null
}

export interface QuoteListData {
  items: QuoteSummary[]
  total: number
  page: number
  limit: number
}

const SENT_CHANNELS = [
  { value: 'email', label: 'Email (manual)' },
  { value: 'linkedin', label: 'LinkedIn (manual)' },
  { value: 'in_person', label: 'In person' },
  { value: 'phone', label: 'Phone' },
  { value: 'portal_manual', label: 'Portal (manual)' },
  { value: 'other', label: 'Other' },
]

export { SENT_CHANNELS }

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

export async function markQuoteSent(id: string, payload: MarkSentPayload): Promise<MarkSentResult> {
  const { data } = await http.post<V1Envelope<MarkSentResult>>(`/v1/quotes/${id}/mark-sent`, payload)
  return data.data
}

export async function fetchDeliveryLogs(quoteId: string): Promise<{ items: DeliveryLog[]; total: number }> {
  const { data } = await http.get<V1Envelope<{ items: DeliveryLog[]; total: number }>>(
    `/v1/quotes/${quoteId}/delivery-logs`,
  )
  return data.data
}

export async function fetchQuoteTimeline(quoteId: string): Promise<{ items: TimelineItem[]; total: number }> {
  const { data } = await http.get<V1Envelope<{ items: TimelineItem[]; total: number }>>(
    `/v1/quotes/${quoteId}/timeline`,
  )
  return data.data
}

export async function fetchQuoteVersions(quoteId: string): Promise<{ items: QuoteVersionSummary[]; total: number }> {
  const { data } = await http.get<V1Envelope<{ items: QuoteVersionSummary[]; total: number }>>(
    `/v1/quotes/${quoteId}/versions`,
  )
  return data.data
}

export async function exportQuotePdf(
  quoteId: string,
  body?: { quote_version_id?: string; export_type?: string },
): Promise<PdfExportResult> {
  const { data } = await http.post<V1Envelope<PdfExportResult>>(`/v1/quotes/${quoteId}/export-pdf`, {
    export_type: 'customer_pdf',
    ...body,
  })
  return data.data
}

export async function fetchQuotePdfExports(quoteId: string): Promise<PdfExportListData> {
  const { data } = await http.get<V1Envelope<PdfExportListData>>(`/v1/quotes/${quoteId}/pdf-exports`)
  return data.data
}

export function quotePdfDownloadUrl(quoteId: string, exportId: string): string {
  return `/api/v1/quotes/${quoteId}/pdf-exports/${exportId}/download`
}
