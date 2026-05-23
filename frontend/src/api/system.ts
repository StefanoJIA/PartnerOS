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
    modules?: { key: string; name: string }[]
    capabilities?: string[]
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
