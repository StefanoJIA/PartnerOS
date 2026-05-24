import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export interface OrderSafety {
  order_created: boolean
  order_confirmed: boolean
  customer_confirmation_recorded: boolean
  production_started: boolean
  shipment_created: boolean
  supplier_notified: boolean
  automatic_sending_enabled: boolean
  inventory_promised: boolean
  certification_promised: boolean
  lead_time_promised: boolean
  payment_received: boolean
}

export interface OrderConfirmationRecord {
  id: string
  order_id: string
  confirmation_type: string
  confirmation_strength: string
  confirmed_by_name: string | null
  confirmed_by_email: string | null
  confirmed_by_company: string | null
  confirmed_at: string | null
  source_channel: string | null
  evidence_reference: string | null
  status: string
  note: string | null
  voided_at: string | null
  voided_reason: string | null
}

export interface OrderLineItem {
  id: string
  source_quote_line_item_id: string
  partner_id: string
  product_name: string
  product_category: string | null
  quantity: number
  unit_price: string
  total_price: string
  currency: string
  incoterm: string | null
  status: string
}

export interface OrderSummary {
  id: string
  order_number: string
  source_quote_id: string
  company_id: string | null
  status: string
  order_date: string
  currency: string
  grand_total: string
  bill_to_company: string | null
  customer_confirmed_at: string | null
  safety: OrderSafety
}

export interface OrderDetail extends OrderSummary {
  source_quote_version_id: string | null
  bill_to_name: string | null
  bill_to_address: string | null
  ship_to_name: string | null
  ship_to_company: string | null
  ship_to_address: string | null
  subtotal: string
  adjustment_total: string
  tax_total: string
  payment_terms: string | null
  shipping_terms: string | null
  internal_notes: string | null
  customer_notes: string | null
  line_items: OrderLineItem[]
  source_quote?: { quote_id: string; quote_number: string; status: string }
  confirmation_summary?: {
    active_count: number
    latest: OrderConfirmationRecord | null
    warnings: string[]
  }
  confirmation?: OrderConfirmationRecord
  warnings?: string[]
  timeline?: OrderTimelineItem[]
}

export interface OrderTimelineItem {
  type: string
  title: string
  timestamp: string | null
  actor?: string
  meta?: Record<string, unknown>
}

export interface OrderListData {
  items: OrderSummary[]
  total: number
  page: number
  limit: number
}

export interface ConfirmCustomerPayload {
  confirmation_type: string
  confirmed_at?: string
  confirmed_by_name?: string
  confirmed_by_email?: string
  confirmed_by_company?: string
  source_channel?: string
  evidence_reference?: string
  note?: string
}

export interface CreateOrderFromQuotePayload {
  quote_id: string
  customer_confirmation?: {
    type: string
    confirmed_at?: string
    note?: string
  }
  internal_notes?: string
  customer_notes?: string
}

export interface ConfirmCustomerResult extends OrderDetail {
  confirmation?: OrderConfirmationRecord
  status_changed?: boolean
}

export async function fetchOrders(params?: {
  status?: string
  quote_id?: string
  search?: string
  page?: number
  limit?: number
}): Promise<OrderListData> {
  const q = new URLSearchParams()
  if (params?.status) q.set('status', params.status)
  if (params?.quote_id) q.set('quote_id', params.quote_id)
  if (params?.search) q.set('search', params.search)
  if (params?.page) q.set('page', String(params.page))
  if (params?.limit) q.set('limit', String(params.limit))
  const suffix = q.toString() ? `?${q}` : ''
  const { data } = await http.get<V1Envelope<OrderListData>>(`/v1/orders${suffix}`)
  return data.data
}

export async function fetchOrder(id: string): Promise<OrderDetail> {
  const { data } = await http.get<V1Envelope<OrderDetail>>(`/v1/orders/${id}`)
  return data.data
}

export async function fetchOrderConfirmations(orderId: string): Promise<{ items: OrderConfirmationRecord[]; total: number }> {
  const { data } = await http.get<V1Envelope<{ items: OrderConfirmationRecord[]; total: number }>>(
    `/v1/orders/${orderId}/confirmations`,
  )
  return data.data
}

export async function createOrderFromQuote(payload: CreateOrderFromQuotePayload): Promise<OrderDetail> {
  const { data } = await http.post<V1Envelope<OrderDetail>>('/v1/orders/from-quote', payload)
  return data.data
}

export async function confirmOrderCustomer(orderId: string, payload: ConfirmCustomerPayload): Promise<ConfirmCustomerResult> {
  const { data } = await http.post<V1Envelope<ConfirmCustomerResult>>(`/v1/orders/${orderId}/confirm-customer`, payload)
  return data.data
}

export async function voidOrderConfirmation(orderId: string, confirmationId: string, reason?: string): Promise<OrderDetail> {
  const { data } = await http.post<V1Envelope<OrderDetail>>(
    `/v1/orders/${orderId}/confirmations/${confirmationId}/void`,
    { reason },
  )
  return data.data
}

export async function cancelOrder(orderId: string, reason?: string): Promise<OrderDetail> {
  const { data } = await http.post<V1Envelope<OrderDetail>>(`/v1/orders/${orderId}/cancel`, { reason })
  return data.data
}

export async function fetchOrderTimeline(orderId: string): Promise<{ items: OrderTimelineItem[]; total: number }> {
  const { data } = await http.get<V1Envelope<{ items: OrderTimelineItem[]; total: number }>>(
    `/v1/orders/${orderId}/timeline`,
  )
  return data.data
}

export function strengthTagType(strength: string): '' | 'success' | 'warning' | 'danger' {
  if (strength === 'strong') return 'success'
  if (strength === 'medium') return 'warning'
  return 'danger'
}

export function confirmationTypeWarning(type: string): string | null {
  if (type === 'verbal') return 'This confirmation type should be reviewed before supplier or production actions.'
  if (type === 'internal_note') return 'This confirmation type should be reviewed before supplier or production actions.'
  return null
}
