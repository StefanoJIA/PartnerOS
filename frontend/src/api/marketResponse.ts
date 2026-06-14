import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export interface MarketResponseSummary {
  feedback_ticket_count: number
  market_signal_count: number
  quote_count: number
  order_count: number
  product_gap_count: number
  recommendation_count: number
  filtered_by_company: boolean
  filtered_by_focus: boolean
  focus_category: string | null
  focus_category_counts: Record<string, number>
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
  focus_category: string | null
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
    focus_category_counts: Record<string, number>
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

export async function fetchMarketResponseIntelligence(params?: { related_company_id?: string; focus_category?: string }) {
  const { data } = await http.get<V1Envelope<MarketResponseIntelligence>>('/v1/market/response-intelligence', { params })
  return data.data
}

export interface MarketResponseReview {
  id: string
  partner_focus: string
  focus_category: string
  product_focus: string[]
  review_dimension: string
  review_dimension_label: string
  visibility_class: string
  visibility_class_label: string
  priority: string
  priority_label: string
  status: string
  status_label: string
  source_type: string
  source_type_label: string
  source_summary: string
  evidence_summary: string | null
  customer_safe_summary: string | null
  internal_notes: string | null
  next_action: string | null
  owner: string | null
  due_date: string | null
  created_at: string
  updated_at: string
}

export interface MarketResponseOption {
  value: string
  label: string
}

export interface MarketResponseReviewConsole {
  status: string
  external_staging_state: string
  reviews: MarketResponseReview[]
  status_options: MarketResponseOption[]
  visibility_options: MarketResponseOption[]
  priority_options: MarketResponseOption[]
  source_type_options: MarketResponseOption[]
  review_dimension_options: MarketResponseOption[]
  status_counts: Record<string, number>
  visibility_counts: Record<string, number>
  partner_counts: Record<string, number>
  safety: {
    manual_review_only: boolean
    customer_safe_whitelist_required: boolean
    raw_token_recorded: boolean
    customer_notified: boolean
    supplier_notified: boolean
    email_sent: boolean
    sms_sent: boolean
    linkedin_sent: boolean
    external_api_called: boolean
    quote_status_changed: boolean
    order_status_changed: boolean
    staging_validated: boolean
    d9_entered: boolean
  }
}

export type MarketResponseReviewPayload = {
  partner_focus: string
  focus_category: string
  product_focus: string[]
  review_dimension: string
  visibility_class: string
  priority: string
  status: string
  source_type: string
  source_summary: string
  evidence_summary?: string | null
  customer_safe_summary?: string | null
  internal_notes?: string | null
  next_action?: string | null
  owner?: string | null
  due_date?: string | null
}

export async function fetchMarketResponseReviews(params?: {
  partner_focus?: string
  focus_category?: string
  visibility_class?: string
  status?: string
}) {
  const { data } = await http.get<V1Envelope<MarketResponseReviewConsole>>('/v1/market/response-reviews', { params })
  return data.data
}

export async function createMarketResponseReview(payload: MarketResponseReviewPayload) {
  const { data } = await http.post<V1Envelope<MarketResponseReviewConsole>>('/v1/market/response-reviews', payload)
  return data.data
}

export async function updateMarketResponseReview(id: string, payload: Partial<MarketResponseReviewPayload>) {
  const { data } = await http.patch<V1Envelope<MarketResponseReviewConsole>>(`/v1/market/response-reviews/${id}`, payload)
  return data.data
}
