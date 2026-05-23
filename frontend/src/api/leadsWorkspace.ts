import { http } from '@/api/http'

export type LeadWorkspaceLead = {
  id: string
  lead_name: string
  company_id: string
  current_stage: string
  lead_type: string
  source: string
  priority?: string | null
  next_action?: string | null
  next_action_due_date?: string | null
  product_interest?: string | null
  owner_user_id?: string | null
}

export type LeadWorkspaceCompany = {
  id: string
  company_name: string
  company_type: string
  website?: string | null
  linkedin_url?: string | null
}

export type LeadWorkspaceContact = {
  id: string
  first_name: string
  last_name: string
  title?: string | null
  email?: string | null
  linkedin_url?: string | null
}

export type LeadWorkspace = {
  lead: LeadWorkspaceLead
  company: LeadWorkspaceCompany
  contact: LeadWorkspaceContact | null
  owner_display: string | null
  related_rfqs: { id: string; rfq_number: string; status: string }[]
  related_samples: { id: string; sample_request_number: string; sample_status: string }[]
  related_orders: {
    id: string
    order_number: string
    production_status: string | null
    risk_level: string | null
  }[]
  related_field_visits: {
    target_id: string
    plan_name: string
    status: string | null
    scheduled_time: string | null
  }[]
  recent_interactions: Record<string, unknown>[]
  open_tasks: {
    id: string
    title: string
    status: string
  }[]
  recent_ai_outputs: { id: string; task_type: string; status: string }[]
}

export async function fetchLeadWorkspace(leadId: string) {
  const { data } = await http.get<LeadWorkspace>(`/leads/${leadId}/workspace`)
  return data
}
