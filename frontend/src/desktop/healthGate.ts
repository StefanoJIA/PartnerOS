/**
 * D1/D4 /health JSON contract — aligned with backend build_health_payload.
 * @see backend/app/core/bootstrap.py
 */

export type HealthStatus = 'ok' | 'degraded' | 'error'
export type BootstrapStatus = 'ready' | 'degraded' | 'error'
export type DatabaseStatus = 'ready' | 'unavailable' | 'not_configured' | 'error'
export type DesktopLaunchPhase = 'loading' | 'ready' | 'degraded' | 'error'

export type DatabaseLifecyclePhase =
  | 'not_configured'
  | 'checking'
  | 'initializing'
  | 'migrating'
  | 'ready'
  | 'error'

export interface HealthPayload {
  status: HealthStatus
  version: string
  runtime_mode: string
  bootstrap_status: BootstrapStatus
  database_status: DatabaseStatus
  database_lifecycle_phase: DatabaseLifecyclePhase
  migration_pending: boolean
  alembic_current_revision: string | null
  alembic_head_revision: string | null
  database_lifecycle_detail?: string
  errors?: string[]
}

const HEALTH_STATUS: HealthStatus[] = ['ok', 'degraded', 'error']
const BOOTSTRAP: BootstrapStatus[] = ['ready', 'degraded', 'error']
const DATABASE: DatabaseStatus[] = ['ready', 'unavailable', 'not_configured', 'error']
const DLM_PHASES: DatabaseLifecyclePhase[] = [
  'not_configured',
  'checking',
  'initializing',
  'migrating',
  'ready',
  'error',
]

const DLM_ACTIVE: DatabaseLifecyclePhase[] = ['checking', 'initializing', 'migrating']

function isStr(v: unknown): v is string {
  return typeof v === 'string' && v.length > 0
}

function isStrOrNull(v: unknown): v is string | null {
  return v === null || typeof v === 'string'
}

export function parseHealthPayload(data: unknown): HealthPayload | null {
  if (!data || typeof data !== 'object') return null
  const o = data as Record<string, unknown>

  if (!HEALTH_STATUS.includes(o.status as HealthStatus)) return null
  if (!isStr(o.version)) return null
  if (!isStr(o.runtime_mode)) return null
  if (!BOOTSTRAP.includes(o.bootstrap_status as BootstrapStatus)) return null
  if (!DATABASE.includes(o.database_status as DatabaseStatus)) return null
  if (!DLM_PHASES.includes(o.database_lifecycle_phase as DatabaseLifecyclePhase)) return null
  if (typeof o.migration_pending !== 'boolean') return null
  if (!isStrOrNull(o.alembic_current_revision)) return null
  if (!isStrOrNull(o.alembic_head_revision)) return null

  const errors = o.errors
  let errList: string[] | undefined
  if (errors !== undefined) {
    if (!Array.isArray(errors) || !errors.every((x) => typeof x === 'string')) return null
    errList = errors as string[]
  }

  let detail: string | undefined
  if (o.database_lifecycle_detail !== undefined) {
    if (typeof o.database_lifecycle_detail !== 'string') return null
    detail = o.database_lifecycle_detail
  }

  return {
    status: o.status as HealthStatus,
    version: o.version,
    runtime_mode: o.runtime_mode,
    bootstrap_status: o.bootstrap_status as BootstrapStatus,
    database_status: o.database_status as DatabaseStatus,
    database_lifecycle_phase: o.database_lifecycle_phase as DatabaseLifecyclePhase,
    migration_pending: o.migration_pending,
    alembic_current_revision: o.alembic_current_revision as string | null,
    alembic_head_revision: o.alembic_head_revision as string | null,
    database_lifecycle_detail: detail,
    errors: errList,
  }
}

export interface LaunchStateInput {
  /** True until first fetch attempt finishes (success or fail). */
  isChecking: boolean
  /** Parsed body when HTTP succeeded and JSON matched contract. */
  health: HealthPayload | null
  /** Network failure, timeout, non-2xx, or malformed body. */
  connectionFailed: boolean
}

const PRODUCT_RUNTIME_MODES = new Set(['desktop', 'demo', 'future_cloud'])

export function isDesktopDatabasePreparing(health: HealthPayload): boolean {
  if (!PRODUCT_RUNTIME_MODES.has(health.runtime_mode)) return false
  return DLM_ACTIVE.includes(health.database_lifecycle_phase)
}

export function resolveDesktopLaunchPhase(input: LaunchStateInput): DesktopLaunchPhase {
  if (input.isChecking) return 'loading'
  if (input.connectionFailed) return 'error'
  if (!input.health) return 'error'
  if (isDesktopDatabasePreparing(input.health)) return 'loading'
  if (input.health.status === 'ok') return 'ready'
  if (input.health.status === 'degraded') return 'degraded'
  return 'error'
}

export function canProceedWhileDegraded(health: HealthPayload): boolean {
  return health.runtime_mode === 'development'
}

export async function fetchHealthPayload(
  url: string,
  msTimeout = 8000,
): Promise<{ connectionFailed: boolean; health: HealthPayload | null }> {
  try {
    const ctrl = new AbortController()
    const t = setTimeout(() => ctrl.abort(), msTimeout)
    const res = await fetch(url, { signal: ctrl.signal })
    clearTimeout(t)
    if (!res.ok) return { connectionFailed: true, health: null }
    let json: unknown
    try {
      json = await res.json()
    } catch {
      return { connectionFailed: true, health: null }
    }
    const parsed = parseHealthPayload(json)
    if (!parsed) return { connectionFailed: true, health: null }
    return { connectionFailed: false, health: parsed }
  } catch {
    return { connectionFailed: true, health: null }
  }
}
