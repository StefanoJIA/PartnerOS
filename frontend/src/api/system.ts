import { http } from '@/api/http'

export interface LegacyHealth {
  status: string
  version?: string
  runtime_mode?: string
  bootstrap_status?: string
  database_status?: string
  database_lifecycle_phase?: string
  migration_pending?: boolean
  alembic_current_revision?: string | null
  alembic_head_revision?: string | null
}

export interface ReadinessEnvelope {
  ok: boolean
  data: {
    ok?: boolean
    service?: string
    database_ready?: boolean
    database_at_head?: boolean
    database_status?: string
    redis_ready?: boolean
    worker_ready?: boolean
    warnings?: string[]
    alembic_current_revision?: string | null
    alembic_head_revision?: string | null
  }
  meta?: { request_id?: string; timestamp?: string }
}

export interface ManifestEnvelope {
  ok: boolean
  data: {
    service_id?: string
    service_name?: string
    version?: string
    api_version?: string
    runtime_mode?: string
    summary_url?: string
    a_domain_status_url?: string
    portal_read_only?: boolean
    automatic_sending_enabled?: boolean
    modules?: { key: string; name: string; frontend_route?: string }[]
    capabilities?: string[]
  }
  meta?: { request_id?: string; timestamp?: string }
}

export interface PortalSummaryEnvelope {
  ok: boolean
  data: {
    service_id?: string
    service_name?: string
    runtime_mode?: string
    api_version?: string
    health?: {
      status?: string
      database_status?: string
      migration_pending?: boolean
    }
    lead_intelligence?: {
      total_leads?: number
      high_priority?: number
      needs_first_outreach?: number
      waiting_for_reply?: number
      follow_up_soon?: number
      needs_contact_research?: number
      needs_enrichment?: number
    }
    segments?: Record<string, number>
    capabilities?: string[]
    warnings?: string[]
  }
  meta?: { request_id?: string; timestamp?: string }
}

export interface ADomainStatusEnvelope {
  ok: boolean
  data: {
    domain?: string
    status?: string
    latest_stage?: string
    daily_workflow_ready?: boolean
    manual_outreach_ready?: boolean
    automatic_sending_enabled?: boolean
    linkedin_automation_enabled?: boolean
    outlook_integration_enabled?: boolean
    database_schema_changed?: boolean
    known_limitations?: string[]
  }
  meta?: { request_id?: string; timestamp?: string }
}

export async function fetchLegacyHealth(): Promise<LegacyHealth> {
  const base = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || ''
  const url = base ? `${base}/health` : '/health'
  const res = await fetch(url)
  if (!res.ok) throw new Error(`GET /health failed (${res.status})`)
  return res.json() as Promise<LegacyHealth>
}

export async function fetchSystemReadiness(): Promise<ReadinessEnvelope> {
  const { data } = await http.get<ReadinessEnvelope>('/v1/system/readiness')
  return data
}

export async function fetchPortalManifest(): Promise<ManifestEnvelope> {
  const { data } = await http.get<ManifestEnvelope>('/v1/portal/manifest')
  return data
}

export async function fetchPortalSummary(): Promise<PortalSummaryEnvelope> {
  const { data } = await http.get<PortalSummaryEnvelope>('/v1/portal/summary')
  return data
}

export async function fetchADomainStatus(): Promise<ADomainStatusEnvelope> {
  const { data } = await http.get<ADomainStatusEnvelope>('/v1/portal/a-domain/status')
  return data
}
