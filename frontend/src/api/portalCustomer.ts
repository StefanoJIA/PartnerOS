import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export interface PortalReadiness {
  enabled: boolean
  require_token: boolean
  token_configured: boolean
  allowed_origins_configured: boolean
  public_base_url_configured: boolean
  public_base_url: string | null
  cors_origins: string[]
  endpoints?: Record<string, string>
  safety: {
    token_exposed: boolean
    automatic_customer_notification: boolean
    forbidden_field_filter_enabled: boolean
  }
}

export interface PortalFieldContract {
  envelope: string[]
  pagination: string[]
  products: string[]
  order_summary: string[]
  order_detail: string[]
  line_item: string[]
  snapshot: string[]
  tracking_summary: string[]
  customer_status: string[]
  customer_next_action: string[]
  customer_status_stages: string[]
  progress_step_states: string[]
  production_item: string[]
  shipment_item: string[]
  resource_item: string[]
  feedback_create: string[]
  feedback_create_response: string[]
  date_policy: {
    planned_dates_are_guarantees: boolean
    planned_dates_label: string
    actual_dates_label: string
  }
}

export interface PortalManifest {
  contract_version: string
  source_of_truth: string
  consumer: string
  public_base_url: string | null
  auth: {
    required: boolean
    header_name: string
    bearer_authorization_supported: boolean
    token_configured: boolean
    token_value_exposed: boolean
  }
  endpoints: Record<string, string>
  field_contract: PortalFieldContract
  customer_visible_surfaces: string[]
  field_policy: {
    allow_customer_visible_fields_only: boolean
    planned_dates_are_guarantees: boolean
    hidden_field_categories: string[]
  }
  safety: {
    token_exposed: boolean
    automatic_customer_notification: boolean
    supplier_notified: boolean
    carrier_api_called: boolean
    order_status_mutated: boolean
    feedback_auto_reply_sent: boolean
  }
}

export interface PortalResult {
  ok: boolean
  status: number
  data: unknown
  forbiddenHits: string[]
}

export interface PortalFeedbackPayload {
  order_id?: string
  company_id?: string
  feedback_type: string
  subject: string
  message: string
  priority: string
  customer_name?: string
  customer_email?: string
}

const FORBIDDEN_MARKERS = [
  'internal_cost',
  'margin',
  'pricing_breakdown',
  'cost_snapshot',
  'supplier_private',
  'supplier_reference',
  'backend_path',
  'storage_key',
  'backend/storage',
  'local_data',
  'portal_customer_api_token',
  'secret_key',
  'password_hash',
]

function portalHeaders(token: string) {
  return token.trim() ? { 'X-Portal-Customer-Token': token.trim() } : {}
}

function forbiddenHits(value: unknown): string[] {
  const raw = JSON.stringify(value).toLowerCase()
  return FORBIDDEN_MARKERS.filter((m) => raw.includes(m))
}

async function callPortal(path: string, token: string, method: 'get' | 'post' = 'get', body?: unknown): Promise<PortalResult> {
  try {
    const res =
      method === 'post'
        ? await http.post<V1Envelope<unknown>>(path, body, { headers: portalHeaders(token), validateStatus: () => true })
        : await http.get<V1Envelope<unknown>>(path, { headers: portalHeaders(token), validateStatus: () => true })
    return { ok: res.status >= 200 && res.status < 300, status: res.status, data: res.data, forbiddenHits: forbiddenHits(res.data) }
  } catch (e) {
    return { ok: false, status: 0, data: e instanceof Error ? e.message : 'Request failed', forbiddenHits: [] }
  }
}

export async function fetchPortalCustomerReadiness(): Promise<PortalReadiness> {
  const { data } = await http.get<V1Envelope<PortalReadiness>>('/v1/portal/customer/readiness')
  return data.data
}

export const portalCustomerContract = {
  manifest: (token: string) => callPortal('/v1/portal/customer/manifest', token),
  products: (token: string) => callPortal('/v1/portal/customer/products', token),
  orders: (token: string) => callPortal('/v1/portal/customer/orders', token),
  orderDetail: (token: string, orderId: string) => callPortal(`/v1/portal/customer/orders/${orderId}`, token),
  orderSnapshot: (token: string, orderId: string) => callPortal(`/v1/portal/customer/orders/${orderId}/snapshot`, token),
  production: (token: string, orderId: string) => callPortal(`/v1/portal/customer/orders/${orderId}/production`, token),
  shipment: (token: string, orderId: string) => callPortal(`/v1/portal/customer/orders/${orderId}/shipment`, token),
  resources: (token: string, orderId: string) => callPortal(`/v1/portal/customer/orders/${orderId}/resources`, token),
  feedback: (token: string, payload: PortalFeedbackPayload) =>
    callPortal('/v1/portal/customer/feedback', token, 'post', payload),
}
