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
}

export interface PricingPreviewResult {
  product_id: string
  quantity: number
  incoterm: string
  pricing_strategy: string
  currency: string
  source: string
  warnings: string[]
  price_breakdown: Record<string, string>
  profit_breakdown: Record<string, string>
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
