import { http } from '@/api/http'

export type EnrichmentRunSummary = {
  id: string
  company_id: string
  status: string
  source_scope: string
  max_pages: number
  pages_fetched: number
  started_at?: string | null
  completed_at?: string | null
  error_message?: string | null
  pending_suggestion_count: number
  created_at: string
}

export type EnrichmentSource = {
  id: string
  url: string
  page_title?: string | null
  page_type: string
  fetch_status: string
  http_status?: number | null
  fetched_at?: string | null
  content_excerpt?: string | null
  content_hash?: string | null
}

export type EnrichmentSuggestion = {
  id: string
  enrichment_run_id: string
  suggestion_type: string
  suggested_value?: string | null
  confidence?: string | null
  reason?: string | null
  evidence_source_id?: string | null
  evidence_snippet?: string | null
  matched_phrase?: string | null
  review_status: string
  reviewed_at?: string | null
  reviewed_by_id?: string | null
}

export type EnrichmentRunDetail = {
  run: EnrichmentRunSummary
  sources: EnrichmentSource[]
  suggestions: EnrichmentSuggestion[]
}

export async function createEnrichmentRun(companyId: string) {
  const { data } = await http.post<EnrichmentRunSummary>(`/companies/${companyId}/enrichment/runs`)
  return data
}

export async function listEnrichmentRuns(companyId: string, limit = 10) {
  const { data } = await http.get<{ items: EnrichmentRunSummary[]; total: number }>(
    `/companies/${companyId}/enrichment/runs`,
    { params: { limit, page: 1 } },
  )
  return data
}

export async function getEnrichmentRunDetail(runId: string) {
  const { data } = await http.get<EnrichmentRunDetail>(`/companies/enrichment/runs/${runId}`)
  return data
}

export async function reviewEnrichmentSuggestion(
  suggestionId: string,
  body: { review_status: 'pending' | 'accepted' | 'rejected' | 'partial'; edited_value?: string | null },
) {
  const { data } = await http.post<EnrichmentSuggestion>(
    `/companies/enrichment/suggestions/${suggestionId}/review`,
    body,
  )
  return data
}

export async function batchReviewEnrichment(
  runId: string,
  suggestionIds: string[],
  review_status: 'accepted' | 'rejected',
) {
  await http.post(`/companies/enrichment/runs/${runId}/suggestions/batch-review`, {
    suggestion_ids: suggestionIds,
    review_status,
  })
}

export async function applyEnrichmentSuggestion(companyId: string, suggestionId: string) {
  const { data } = await http.post<EnrichmentSuggestion>(
    `/companies/${companyId}/enrichment/suggestions/${suggestionId}/apply`,
  )
  return data
}
