import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export interface OrderSafety {
  order_created: boolean
  order_confirmed: boolean
  customer_confirmation_recorded: boolean
  supplier_confirmation_recorded: boolean
  production_started: boolean
  shipment_created: boolean
  supplier_notified: boolean
  automatic_sending_enabled: boolean
  inventory_promised: boolean
  certification_promised: boolean
  lead_time_promised: boolean
  payment_received: boolean
  customer_notified?: boolean
  milestone_updated?: boolean
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
  partner_splits_summary?: {
    total_splits: number
    confirmed_splits: number
    pending_splits: number
    needs_clarification_splits: number
  }
  supplier_confirmation_summary?: {
    active_confirmations: number
    confirmed_count: number
    needs_clarification_count: number
    rejected_count: number
  }
  production_summary?: {
    total_milestones: number
    completed_milestones: number
    in_progress_milestones: number
    delayed_milestones: number
    blocked_milestones: number
    ready_to_ship_completed: boolean
    shipment_created: boolean
  }
  shipment_summary?: {
    total_plans: number
    active_plans: number
    shipped_plans: number
    delivered_plans: number
    shipment_created: boolean
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

export interface ProductionMilestone {
  id: string
  order_id: string
  partner_split_id: string
  partner_id: string
  milestone_type: string
  milestone_label: string
  sequence: number
  status: string
  planned_date: string | null
  actual_date: string | null
  responsible_party: string | null
  source: string
  notes: string | null
}

export interface ShipmentPlan {
  id: string
  order_id: string
  partner_split_id: string | null
  shipment_method: string | null
  incoterm: string | null
  origin: string | null
  destination: string | null
  estimated_ship_date: string | null
  estimated_arrival_date: string | null
  tracking_number: string | null
  status: string
  notes: string | null
  portal_visible_fields?: {
    status: string
    shipment_method: string | null
    estimated_ship_date: string | null
    estimated_arrival_date: string | null
    tracking_number: string | null
  }
  safety?: {
    shipment_created: boolean
    supplier_notified: boolean
    customer_notified: boolean
  }
}

export interface OrderResource {
  id: string
  order_id: string
  file_id: string
  title: string
  category: string
  description: string | null
  status: string
  customer_visible: boolean
  published_at: string | null
  filename: string
  mime: string | null
  size: number
  created_at: string | null
  updated_at: string | null
  download_url?: string
  download_expires_at?: number
  safety: {
    customer_visible: boolean
    download_link_signed: boolean
    file_location_exposed: boolean
    filesystem_path_exposed: boolean
    customer_notified: boolean
    automatic_email_sent: boolean
  }
}

export interface PartnerSplit {
  id: string
  order_id: string
  partner_id: string
  partner_name: string
  split_number: string
  split_status: string
  supplier_confirmation_status: string
  supplier_confirmed_at: string | null
  expected_production_start: string | null
  expected_ready_date: string | null
  line_item_count: number
  subtotal: string
  currency: string
  notes: string | null
  production_milestone_count?: number
  production_completed_count?: number
  current_milestone?: ProductionMilestone | null
  next_milestone?: ProductionMilestone | null
  line_items?: OrderLineItem[]
  supplier_confirmations?: SupplierConfirmationRecord[]
}

export interface SupplierConfirmationRecord {
  id: string
  order_id: string
  partner_split_id: string
  partner_id: string
  confirmation_status: string
  confirmed_at: string | null
  confirmed_by_name: string | null
  confirmed_by_email: string | null
  confirmation_channel: string | null
  inventory_confirmed: boolean
  certification_confirmed: boolean
  lead_time_confirmed: boolean
  production_capacity_confirmed: boolean
  expected_production_start: string | null
  expected_ready_date: string | null
  supplier_reference: string | null
  note: string | null
  status: string
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

export async function ensurePartnerSplits(orderId: string): Promise<OrderDetail & { splits?: PartnerSplit[]; warnings?: string[] }> {
  const { data } = await http.post<V1Envelope<OrderDetail & { splits?: PartnerSplit[]; warnings?: string[] }>>(
    `/v1/orders/${orderId}/partner-splits/ensure`,
    {},
  )
  return data.data
}

export async function fetchPartnerSplits(orderId: string): Promise<{ items: PartnerSplit[]; total: number }> {
  const { data } = await http.get<V1Envelope<{ items: PartnerSplit[]; total: number }>>(
    `/v1/orders/${orderId}/partner-splits`,
  )
  return data.data
}

export async function fetchPartnerSplitDetail(orderId: string, splitId: string): Promise<PartnerSplit> {
  const { data } = await http.get<V1Envelope<PartnerSplit>>(`/v1/orders/${orderId}/partner-splits/${splitId}`)
  return data.data
}

export interface SupplierConfirmationPayload {
  confirmation_status: string
  confirmed_at?: string
  confirmed_by_name?: string
  confirmed_by_email?: string
  confirmation_channel?: string
  inventory_confirmed?: boolean
  certification_confirmed?: boolean
  lead_time_confirmed?: boolean
  production_capacity_confirmed?: boolean
  expected_production_start?: string
  expected_ready_date?: string
  supplier_reference?: string
  note?: string
}

export async function addSupplierConfirmation(
  orderId: string,
  splitId: string,
  payload: SupplierConfirmationPayload,
): Promise<PartnerSplit & { confirmation?: SupplierConfirmationRecord; warnings?: string[] }> {
  const { data } = await http.post<
    V1Envelope<PartnerSplit & { confirmation?: SupplierConfirmationRecord; warnings?: string[] }>
  >(`/v1/orders/${orderId}/partner-splits/${splitId}/supplier-confirmations`, payload)
  return data.data
}

export async function fetchSupplierConfirmations(
  orderId: string,
): Promise<{ items: SupplierConfirmationRecord[]; total: number }> {
  const { data } = await http.get<V1Envelope<{ items: SupplierConfirmationRecord[]; total: number }>>(
    `/v1/orders/${orderId}/supplier-confirmations`,
  )
  return data.data
}

export async function voidSupplierConfirmation(
  orderId: string,
  confirmationId: string,
  reason?: string,
): Promise<PartnerSplit> {
  const { data } = await http.post<V1Envelope<PartnerSplit>>(
    `/v1/orders/${orderId}/supplier-confirmations/${confirmationId}/void`,
    { reason },
  )
  return data.data
}

export const SUPPLIER_SAFETY_NOTE =
  'Recording supplier confirmation does not notify suppliers, start production, create shipments, or guarantee inventory, certifications, or lead times unless explicitly confirmed by the supplier and manually recorded.'

export const PRODUCTION_SAFETY_NOTE =
  'Production milestones are internal planning and tracking records. They do not create shipments, notify suppliers or customers, or guarantee lead time.'

export const SHIPMENT_SAFETY_NOTE =
  'Shipment plans are manually maintained logistics records. They do not create shipments, notify suppliers or customers, call carrier APIs, or change the order status.'

export async function ensureProductionMilestones(orderId: string, splitId: string): Promise<OrderDetail & { milestones?: ProductionMilestone[] }> {
  const { data } = await http.post<V1Envelope<OrderDetail & { milestones?: ProductionMilestone[] }>>(
    `/v1/orders/${orderId}/partner-splits/${splitId}/production-milestones/ensure`,
    {},
  )
  return data.data
}

export async function fetchProductionMilestones(
  orderId: string,
  splitId?: string,
): Promise<{ items: ProductionMilestone[]; total: number }> {
  const path = splitId
    ? `/v1/orders/${orderId}/partner-splits/${splitId}/production-milestones`
    : `/v1/orders/${orderId}/production-milestones`
  const { data } = await http.get<V1Envelope<{ items: ProductionMilestone[]; total: number }>>(path)
  return data.data
}

export interface ProductionMilestoneUpdatePayload {
  status?: string
  planned_date?: string
  actual_date?: string
  responsible_party?: string
  notes?: string
}

export async function updateProductionMilestone(
  orderId: string,
  milestoneId: string,
  payload: ProductionMilestoneUpdatePayload,
): Promise<ProductionMilestone & { warnings?: string[] }> {
  const { data } = await http.patch<V1Envelope<ProductionMilestone & { warnings?: string[] }>>(
    `/v1/orders/${orderId}/production-milestones/${milestoneId}`,
    payload,
  )
  return data.data
}

export interface ShipmentPlanPayload {
  partner_split_id?: string
  shipment_method?: string
  incoterm?: string
  origin?: string
  destination?: string
  estimated_ship_date?: string
  estimated_arrival_date?: string
  tracking_number?: string
  status?: string
  notes?: string
}

export async function fetchShipmentPlans(orderId: string): Promise<{ items: ShipmentPlan[]; total: number }> {
  const { data } = await http.get<V1Envelope<{ items: ShipmentPlan[]; total: number }>>(
    `/v1/orders/${orderId}/shipment-plans`,
  )
  return data.data
}

export async function createShipmentPlan(orderId: string, payload: ShipmentPlanPayload): Promise<ShipmentPlan> {
  const { data } = await http.post<V1Envelope<ShipmentPlan>>(`/v1/orders/${orderId}/shipment-plans`, payload)
  return data.data
}

export async function updateShipmentPlan(
  orderId: string,
  planId: string,
  payload: ShipmentPlanPayload,
): Promise<ShipmentPlan> {
  const { data } = await http.patch<V1Envelope<ShipmentPlan>>(
    `/v1/orders/${orderId}/shipment-plans/${planId}`,
    payload,
  )
  return data.data
}

export interface OrderResourcePayload {
  file_id?: string
  title?: string
  category?: string
  description?: string
  status?: string
  customer_visible?: boolean
}

export async function fetchOrderResources(orderId: string): Promise<{ items: OrderResource[]; total: number }> {
  const { data } = await http.get<V1Envelope<{ items: OrderResource[]; total: number }>>(
    `/v1/orders/${orderId}/resources`,
  )
  return data.data
}

export async function createOrderResource(orderId: string, payload: OrderResourcePayload): Promise<OrderResource> {
  const { data } = await http.post<V1Envelope<OrderResource>>(`/v1/orders/${orderId}/resources`, payload)
  return data.data
}

export async function updateOrderResource(
  orderId: string,
  resourceId: string,
  payload: OrderResourcePayload,
): Promise<OrderResource> {
  const { data } = await http.patch<V1Envelope<OrderResource>>(
    `/v1/orders/${orderId}/resources/${resourceId}`,
    payload,
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
