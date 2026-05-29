import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export interface PortalReadiness {
  enabled: boolean
  require_token: boolean
  token_configured: boolean
  allowed_origins_configured: boolean
  cors_origins: string[]
  safety: {
    token_exposed: boolean
    automatic_customer_notification: boolean
    forbidden_field_filter_enabled: boolean
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
  'storage_key',
  'backend/storage',
  'portal_customer_api_token',
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
  products: (token: string) => callPortal('/v1/portal/customer/products', token),
  orders: (token: string) => callPortal('/v1/portal/customer/orders', token),
  orderDetail: (token: string, orderId: string) => callPortal(`/v1/portal/customer/orders/${orderId}`, token),
  production: (token: string, orderId: string) => callPortal(`/v1/portal/customer/orders/${orderId}/production`, token),
  shipment: (token: string, orderId: string) => callPortal(`/v1/portal/customer/orders/${orderId}/shipment`, token),
  resources: (token: string, orderId: string) => callPortal(`/v1/portal/customer/orders/${orderId}/resources`, token),
  feedback: (token: string, payload: PortalFeedbackPayload) =>
    callPortal('/v1/portal/customer/feedback', token, 'post', payload),
}
