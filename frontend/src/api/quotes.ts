// Frontend API for D6.3+ Customer Quotes.

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

export interface QuoteLearningSafety {
  external_message_sent: boolean
  quote_status_changed: boolean
  order_status_changed: boolean
  customer_notified: boolean
  supplier_notified: boolean
  raw_token_recorded: boolean
  customer_forbidden_fields_exposed: boolean
}

export interface QuoteLearningRecord {
  id: string
  quote_id: string
  quote_version_id: string | null
  outcome_status: string
  customer_feedback: string | null
  customer_objection: string | null
  competitor_signal: string | null
  won_reason: string | null
  lost_reason: string | null
  price_feedback: string | null
  delivery_feedback: string | null
  product_feedback: Record<string, unknown>
  product_dimensions: string[]
  next_action: string | null
  owner: string | null
  follow_up_date: string | null
  affects_product_intelligence: boolean
  affects_market_response: boolean
  affects_opportunity: boolean
  internal_only: boolean
  created_at: string | null
  updated_at: string | null
  safety: QuoteLearningSafety
}

export interface QuoteLearningPayload {
  quote_version_id?: string | null
  outcome_status: string
  customer_feedback?: string | null
  customer_objection?: string | null
  competitor_signal?: string | null
  won_reason?: string | null
  lost_reason?: string | null
  price_feedback?: string | null
  delivery_feedback?: string | null
  product_feedback?: Record<string, unknown> | null
  product_dimensions?: string[]
  next_action?: string | null
  owner?: string | null
  follow_up_date?: string | null
  affects_product_intelligence?: boolean
  affects_market_response?: boolean
  affects_opportunity?: boolean
  internal_only?: boolean
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
  latest_learning?: QuoteLearningRecord | null
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

export async function fetchQuoteLearning(quoteId: string): Promise<{ items: QuoteLearningRecord[]; total: number; safety: QuoteLearningSafety }> {
  const { data } = await http.get<V1Envelope<{ items: QuoteLearningRecord[]; total: number; safety: QuoteLearningSafety }>>(
    `/v1/quotes/${quoteId}/learning`,
  )
  return data.data
}

export async function createQuoteLearning(quoteId: string, payload: QuoteLearningPayload): Promise<QuoteLearningRecord> {
  const { data } = await http.post<V1Envelope<QuoteLearningRecord>>(`/v1/quotes/${quoteId}/learning`, payload)
  return data.data
}

export async function updateQuoteLearning(
  quoteId: string,
  learningId: string,
  payload: Partial<QuoteLearningPayload>,
): Promise<QuoteLearningRecord> {
  const { data } = await http.patch<V1Envelope<QuoteLearningRecord>>(`/v1/quotes/${quoteId}/learning/${learningId}`, payload)
  return data.data
}

export async function deleteQuote(id: string): Promise<{ archived: boolean; id: string }> {
  const { data } = await http.delete<V1Envelope<{ archived: boolean; id: string }>>(`/v1/quotes/${id}`)
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

export type ReadinessStatus =
  | 'ready_for_order_review'
  | 'needs_customer_confirmation'
  | 'needs_internal_review'
  | 'not_ready'

export interface ReadinessChecklistItem {
  key: string
  label: string
  status: 'pass' | 'warning' | 'fail'
  details?: string
}

export interface OrderReadinessSafety {
  order_created: boolean
  production_started: boolean
  shipment_created: boolean
  automatic_sending_enabled: boolean
  inventory_promised?: boolean
  certification_promised?: boolean
  lead_time_promised?: boolean
}

export interface OrderReadiness {
  quote_id: string
  quote_number: string
  readiness_status: ReadinessStatus
  readiness_score: number
  blocking_items: string[]
  warning_items: string[]
  checklist: ReadinessChecklistItem[]
  order_input_contract: Record<string, unknown>
  recommended_next_action: string
  safety: OrderReadinessSafety
}

export async function fetchOrderReadiness(quoteId: string): Promise<OrderReadiness> {
  const { data } = await http.get<V1Envelope<OrderReadiness>>(`/v1/quotes/${quoteId}/order-readiness`)
  return data.data
}
