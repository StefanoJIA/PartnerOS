import { http } from '@/api/http'

export type ProductOpportunityBoardSummary = {
  total: number
  high_opportunity: number
  promising: number
  quote_ready: number
  almost_ready: number
  almost_quote_ready: number
  sample_ready: number
  needs_specs: number
  lifting_system_fit: number
  project_supply_fit: number
  education_fit: number
  medical_fit: number
  oem_odm_fit: number
  oem_odm_potential: number
}

export type ProductOpportunityBoardRowRaw = {
  lead_id: string
  company_name: string
  project_opportunity_score: number
  opportunity_score?: number
  opportunity_level: string
  project_type: string
  quote_readiness: string
  sample_readiness: string
  recommended_product_focus?: string[]
  missing_quote_info?: string[]
  recommended_next_product_action?: string | null
  sales_angle?: string | null
  next_action?: string | null
  follow_up_date?: string | null
  due_status?: string | null
}

export type ProductOpportunityBoardResponse = {
  summary: ProductOpportunityBoardSummary
  missing_info_summary: Record<string, number>
  rows: ProductOpportunityBoardRowRaw[]
  safety: {
    automatic_quote_creation: boolean
    automatic_sending_enabled: boolean
    price_promises_enabled: boolean
    inventory_promises_enabled: boolean
  }
  warnings: string[]
  degraded: boolean
}

export async function fetchProductOpportunityBoard() {
  const { data } = await http.get<ProductOpportunityBoardResponse>('/a-domain/product-opportunity-board')
  return data
}
