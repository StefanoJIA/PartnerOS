import { http } from '@/api/http'
import type { ProductAwareDraft } from '@/constants/productAwareDraft'

export type ProductAwareDraftRequest = {
  channel: string
  draft_purpose: string
  tone?: string
  language?: string
  include_questions?: boolean
  include_product_brief?: boolean
}

export async function fetchProductAwareDraft(leadId: string, body: ProductAwareDraftRequest) {
  const { data } = await http.post<ProductAwareDraft>(
    `/a-domain/leads/${leadId}/product-aware-draft`,
    body,
  )
  return data
}
