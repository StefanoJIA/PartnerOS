import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export interface FeedbackTicketSafety {
  customer_notified: boolean
  automatic_reply_sent: boolean
  email_sent: boolean
  sla_promised: boolean
}

export interface FeedbackTicket {
  id: string
  ticket_number: string
  source: string
  order_id: string | null
  company_id: string | null
  feedback_type: string
  subject: string
  message: string
  status: string
  priority: string
  internal_owner: string | null
  customer_name: string | null
  customer_email: string | null
  response_summary: string | null
  created_at: string
  updated_at: string
  operation: {
    internal_handling_only: boolean
    activity_logging_enabled: boolean
    customer_visible_response: boolean
    age_days: number | null
    open: boolean
    needs_internal_review: boolean
    response_summary_missing: boolean
  }
  safety: FeedbackTicketSafety
}

export interface FeedbackTicketList {
  items: FeedbackTicket[]
  total: number
  page: number
  limit: number
}

export interface FeedbackTicketUpdatePayload {
  status?: string
  priority?: string
  internal_owner?: string | null
  response_summary?: string | null
}

export async function fetchFeedbackTickets(params?: {
  status?: string
  priority?: string
  feedback_type?: string
  search?: string
  page?: number
  limit?: number
}): Promise<FeedbackTicketList> {
  const q = new URLSearchParams()
  if (params?.status) q.set('status', params.status)
  if (params?.priority) q.set('priority', params.priority)
  if (params?.feedback_type) q.set('feedback_type', params.feedback_type)
  if (params?.search) q.set('search', params.search)
  if (params?.page) q.set('page', String(params.page))
  if (params?.limit) q.set('limit', String(params.limit))
  const suffix = q.toString() ? `?${q}` : ''
  const { data } = await http.get<V1Envelope<FeedbackTicketList>>(`/v1/feedback-tickets${suffix}`)
  return data.data
}

export async function fetchFeedbackTicket(id: string): Promise<FeedbackTicket> {
  const { data } = await http.get<V1Envelope<FeedbackTicket>>(`/v1/feedback-tickets/${id}`)
  return data.data
}

export async function updateFeedbackTicket(
  id: string,
  payload: FeedbackTicketUpdatePayload,
): Promise<FeedbackTicket> {
  const { data } = await http.patch<V1Envelope<FeedbackTicket>>(`/v1/feedback-tickets/${id}`, payload)
  return data.data
}

export const FEEDBACK_SAFETY_NOTE =
  'Feedback operations are internal notes only. PartnerOS does not send email, notify customers, or promise an SLA from this console.'
