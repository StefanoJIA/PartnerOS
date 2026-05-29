import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export interface PartnerOperationsSummary {
  partner_count: number
  split_count: number
  order_count: number
  supplier_confirmed_split_count: number
  supplier_open_split_count: number
  delayed_milestone_count: number
  blocked_milestone_count: number
  active_shipment_count: number
  shipped_or_delivered_count: number
}

export interface PartnerOperationsRow {
  partner_id: string
  partner_name: string
  partner_type: string | null
  split_count: number
  order_count: number
  line_item_count: number
  subtotal_by_currency: Record<string, string>
  supplier_confirmation_status_counts: Record<string, number>
  split_status_counts: Record<string, number>
  milestone_status_counts: Record<string, number>
  delayed_milestone_count: number
  blocked_milestone_count: number
  ready_to_ship_completed_count: number
  shipment_status_counts: Record<string, number>
  active_shipment_count: number
  next_expected_ready_date: string | null
  risk_flags: string[]
}

export interface PartnerOperationsDashboard {
  summary: PartnerOperationsSummary
  items: PartnerOperationsRow[]
  total: number
  safety: {
    read_only: boolean
    supplier_notified: boolean
    customer_notified: boolean
    shipment_created: boolean
    order_status_changed: boolean
    automatic_sending_enabled: boolean
  }
}

export async function fetchPartnerOperationsDashboard() {
  const { data } = await http.get<V1Envelope<PartnerOperationsDashboard>>('/v1/operations/partner-dashboard')
  return data.data
}
