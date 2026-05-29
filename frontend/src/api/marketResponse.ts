import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export interface MarketResponseSummary {
  feedback_ticket_count: number
  market_signal_count: number
  quote_count: number
  order_count: number
  product_gap_count: number
  recommendation_count: number
}

export interface FeedbackSignal {
  ticket_id: string
  ticket_number: string
  feedback_type: string
  status: string
  priority: string
  subject: string
  summary: string
  tags: string[]
  linked_order_id: string | null
  human_review_required: boolean
  created_at: string | null
}

export interface DemandSignalRow {
  category: string
  market_signal_count: number
  feedback_signal_count: number
  quote_line_count: number
  order_line_count: number
  quoted_quantity: number
  ordered_quantity: number
  importance_counts: Record<string, number>
  segments: Record<string, number>
  adjustable_frame_focus: boolean
}

export interface ProductGapRow {
  product_id: string
  product_name: string
  category: string
  missing_fields: string[]
  demand_signal_count: number
  recommended_review: string
  human_review_required: boolean
}

export interface WinLossCategoryRow {
  category: string
  quote_count: number
  quoted_quantity: number
  quoted_value: string
  order_count: number
  ordered_quantity: number
  ordered_value: string
  win_count: number
  loss_count: number
  open_count: number
  win_rate: number | null
}

export interface MarketRecommendation {
  area: string
  priority: string
  recommendation: string
  evidence: string
  human_review_required: boolean
  auto_execute: boolean
}

export interface MarketResponseIntelligence {
  summary: MarketResponseSummary
  feedback: {
    total: number
    status_counts: Record<string, number>
    priority_counts: Record<string, number>
    type_counts: Record<string, number>
    tag_counts: Record<string, number>
    items: FeedbackSignal[]
  }
  win_loss: {
    quote_status_counts: Record<string, number>
    order_status_counts: Record<string, number>
    won_quote_count: number
    lost_quote_count: number
    open_quote_count: number
    category_rows: WinLossCategoryRow[]
  }
  demand: {
    items: DemandSignalRow[]
    total: number
  }
  product_gaps: {
    items: ProductGapRow[]
    total: number
    missing_field_counts: Record<string, number>
  }
  recommendations: MarketRecommendation[]
  safety: {
    read_only: boolean
    ai_suggestions_advisory: boolean
    human_review_required: boolean
    ai_executed: boolean
    customer_notified: boolean
    supplier_notified: boolean
    email_sent: boolean
    webhook_sent: boolean
    partner_selection_changed: boolean
    quote_status_changed: boolean
    order_status_changed: boolean
  }
}

export async function fetchMarketResponseIntelligence() {
  const { data } = await http.get<V1Envelope<MarketResponseIntelligence>>('/v1/market/response-intelligence')
  return data.data
}
