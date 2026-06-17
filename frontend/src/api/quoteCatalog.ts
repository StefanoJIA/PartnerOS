// Frontend API for D6.2 quote catalog.

import { http } from '@/api/http'

export interface CatalogProduct {
  id: string
  partner_id: string
  internal_sku: string
  partner_product_code: string | null
  product_name: string
  product_category: string
  product_family: string | null
  description_customer: string | null
  status: string
  attributes_json: Record<string, unknown> | null
}

export interface V1Envelope<T> {
  ok: boolean
  data: T
  meta?: { request_id?: string }
}

export interface ProductListData {
  items: CatalogProduct[]
  total: number
  page: number
  limit: number
}

export interface PricingPreviewRequest {
  product_id: string
  quantity: number
  incoterm: string
  pricing_strategy: string
  discount?: { type: string; value: number }
  fx_rate_date?: string
  manual_unit_price?: number
}

export interface QuoteModelStage {
  [key: string]: unknown
}

export interface IntervalQuoteRow {
  min_qty: number
  max_qty: number | null
  quantity_label: string
  currency: string
  fob_unit_price: string | null
  ddp_unit_price: string | null
  incoterms_available: string[]
  pricing_strategies?: string[]
  customer_visible?: boolean
}

export interface QuoteModelSnapshot {
  workflow: Array<{ step: string; workbook_sheet: string; status: string }>
  product: { id: string; name: string; category: string; family: string | null }
  inputs: QuoteModelStage
  fx_stage: QuoteModelStage
  cost_stage: QuoteModelStage
  logistics_stage: QuoteModelStage
  pricing_stage: QuoteModelStage
  discount_stage: QuoteModelStage
  final_quote_stage: QuoteModelStage
  profit_stage: QuoteModelStage
  customer_safe_boundary: string
  warnings: string[]
  safety: {
    quote_created: boolean
    automatic_sending_enabled: boolean
    inventory_promised: boolean
    certification_promised: boolean
    lead_time_promised: boolean
  }
}

export interface PricingPreviewResult {
  product_id: string
  quantity: number
  incoterm: string
  pricing_strategy: string
  currency: string
  source: string
  warnings: string[]
  fx_rate_used?: QuoteModelStage | null
  cost_breakdown: Record<string, string>
  price_breakdown: Record<string, string>
  profit_breakdown: Record<string, string>
  quote_model?: QuoteModelSnapshot
  safety: {
    quote_created: boolean
    automatic_sending_enabled: boolean
    inventory_promised: boolean
    certification_promised: boolean
    lead_time_promised: boolean
  }
}

export async function fetchCatalogProducts(params?: {
  partner_id?: string
  category?: string
  search?: string
  limit?: number
}) {
  const { data } = await http.get<V1Envelope<ProductListData>>('/v1/products', { params })
  return data.data
}

export async function postPricingPreview(body: PricingPreviewRequest) {
  const { data } = await http.post<V1Envelope<PricingPreviewResult>>('/v1/quotes/pricing/preview', body)
  return data.data
}
