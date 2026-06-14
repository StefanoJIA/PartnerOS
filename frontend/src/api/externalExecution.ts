import { http } from '@/api/http'
import type { V1Envelope } from '@/api/quotes'

export type ExternalActionStatus =
  | 'draft'
  | 'ready to send'
  | 'sent manually'
  | 'response received'
  | 'blocked'
  | 'complete'

export interface ExternalExecutionAction {
  id: string
  action_type: string
  target_partner_system: string
  partner_focus: string | null
  product_focus: string[]
  owner: string | null
  due_date: string | null
  dependency: string | null
  next_step: string | null
  status: ExternalActionStatus
  status_label: string
  response_summary: string | null
  risk_notes: string | null
  blocker_notes: string | null
  redacted_credential_status: string | null
  staging_readiness_key: string | null
  pilot_readiness_key: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface ExternalExecutionActionPayload {
  action_type?: string
  target_partner_system?: string
  partner_focus?: string | null
  product_focus?: string[]
  owner?: string | null
  due_date?: string | null
  dependency?: string | null
  next_step?: string | null
  status?: ExternalActionStatus
  response_summary?: string | null
  risk_notes?: string | null
  blocker_notes?: string | null
  redacted_credential_status?: string | null
  staging_readiness_key?: string | null
  pilot_readiness_key?: string | null
  notes?: string | null
}

export interface ReadinessRow {
  item: string
  status: string
  detail: string
  next_action?: string
  linked_action_ids?: string[]
  linked_action_statuses?: string[]
}

export interface HosunFieldReviewRow {
  field: string
  review_class: string
  rule: string
}

export interface PartnerCoverageRow {
  partner: string
  focus: string
  rule: string
}

export interface ExternalExecutionConsole {
  status: string
  external_staging_state: string
  actions: ExternalExecutionAction[]
  status_options: Array<{ value: ExternalActionStatus; label: string }>
  status_counts: Record<string, number>
  staging_readiness: ReadinessRow[]
  lifting_systems_field_review: HosunFieldReviewRow[]
  partner_coverage: PartnerCoverageRow[]
  safety: Record<string, boolean>
}

export async function fetchExternalExecutionConsole(): Promise<ExternalExecutionConsole> {
  const { data } = await http.get<V1Envelope<ExternalExecutionConsole>>('/v1/external-execution/console')
  return data.data
}

export async function createExternalExecutionAction(
  payload: Required<Pick<ExternalExecutionActionPayload, 'action_type' | 'target_partner_system'>> &
    ExternalExecutionActionPayload,
): Promise<ExternalExecutionConsole> {
  const { data } = await http.post<V1Envelope<ExternalExecutionConsole>>('/v1/external-execution/actions', payload)
  return data.data
}

export async function updateExternalExecutionAction(
  id: string,
  payload: ExternalExecutionActionPayload,
): Promise<ExternalExecutionConsole> {
  const { data } = await http.patch<V1Envelope<ExternalExecutionConsole>>(`/v1/external-execution/actions/${id}`, payload)
  return data.data
}
