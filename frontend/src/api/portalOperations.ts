import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export interface PortalOperationsConsole {
  status: {
    ready: boolean
    enabled: boolean
    token_required: boolean
    token_configured: boolean
    public_base_url_configured: boolean
    public_base_url: string | null
    allowed_origins: string[]
    missing_config: string[]
  }
  endpoint_readiness: Record<'products' | 'orders' | 'production' | 'shipment' | 'resources' | 'feedback', boolean>
  recent_customer_visible_orders: {
    items: Array<{
      id: string
      order_number: string
      status: string
      company_name: string | null
      grand_total: string | null
      currency: string
    }>
    total: number
  }
  customer_snapshots: Array<{
    order: { id: string; order_number: string; status: string }
    customer_status: {
      stage: string
      label: string
      production_completed: boolean
      ready_to_ship: boolean
      shipped: boolean
      delivered: boolean
      planned_dates_are_guarantees: boolean
    }
    shipment: { status_counts: Record<string, number>; active_count: number }
    feedback: { open_count: number; customer_notified: boolean; automatic_reply_sent: boolean }
    safety: { forbidden_field_filter_enabled: boolean; token_exposed: boolean }
  }>
  shipment_status_counts: Record<string, number>
  feedback_status_counts: Record<string, number>
  feedback_priority_counts: Record<string, number>
  recent_feedback_tickets: Array<{
    id: string
    ticket_number: string
    order_id: string | null
    feedback_type: string
    subject: string
    status: string
    priority: string
    created_at: string | null
  }>
  forbidden_field_audit: {
    checked: boolean
    hits: string[]
    credential_value_exposed: boolean
    server_file_path_exposed: boolean
    cost_fields_exposed: boolean
  }
  safety: {
    read_only: boolean
    customer_notified: boolean
    supplier_notified: boolean
    automatic_reply_sent: boolean
    carrier_api_called: boolean
    order_status_mutated: boolean
  }
}

export async function fetchPortalOperationsConsole(): Promise<PortalOperationsConsole> {
  const { data } = await http.get<V1Envelope<PortalOperationsConsole>>('/v1/portal/operations/console')
  return data.data
}
