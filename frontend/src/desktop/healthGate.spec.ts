import { describe, expect, it, vi } from 'vitest'
import {
  type HealthPayload,
  fetchHealthPayload,
  parseHealthPayload,
  resolveDesktopLaunchPhase,
  canProceedWhileDegraded,
} from './healthGate'

const valid: HealthPayload = {
  status: 'ok',
  version: '0.1.0',
  runtime_mode: 'development',
  bootstrap_status: 'ready',
  database_status: 'ready',
  database_lifecycle_phase: 'ready' as const,
  migration_pending: false,
  alembic_current_revision: null,
  alembic_head_revision: null,
}

describe('parseHealthPayload', () => {
  it('accepts minimal valid D1/D4 payload', () => {
    const p = parseHealthPayload({ ...valid })
    expect(p).toMatchObject(valid)
  })

  it('accepts errors array', () => {
    const p = parseHealthPayload({ ...valid, errors: ['x'] })
    expect(p?.errors).toEqual(['x'])
  })

  it('accepts lifecycle detail', () => {
    const p = parseHealthPayload({
      ...valid,
      database_lifecycle_detail: 'alembic upgrade head',
    })
    expect(p?.database_lifecycle_detail).toBe('alembic upgrade head')
  })

  it('rejects invalid status', () => {
    expect(parseHealthPayload({ ...valid, status: 'nice' })).toBeNull()
  })

  it('rejects bad errors field', () => {
    expect(parseHealthPayload({ ...valid, errors: 'no' })).toBeNull()
  })

  it('rejects missing DLM fields', () => {
    const { database_lifecycle_phase: _p, ...rest } = valid
    expect(parseHealthPayload(rest)).toBeNull()
  })
})

describe('resolveDesktopLaunchPhase', () => {
  it('returns loading while checking', () => {
    expect(
      resolveDesktopLaunchPhase({
        isChecking: true,
        health: null,
        connectionFailed: false,
      }),
    ).toBe('loading')
  })

  it('connection failure is error, not degraded', () => {
    expect(
      resolveDesktopLaunchPhase({
        isChecking: false,
        health: null,
        connectionFailed: true,
      }),
    ).toBe('error')
  })

  it('maps ok to ready', () => {
    expect(
      resolveDesktopLaunchPhase({
        isChecking: false,
        health: { ...valid },
        connectionFailed: false,
      }),
    ).toBe('ready')
  })

  it('keeps desktop in loading while DLM migrates', () => {
    expect(
      resolveDesktopLaunchPhase({
        isChecking: false,
        health: {
          ...valid,
          runtime_mode: 'desktop',
          status: 'degraded',
          bootstrap_status: 'degraded',
          database_lifecycle_phase: 'migrating',
          migration_pending: true,
        },
        connectionFailed: false,
      }),
    ).toBe('loading')
  })
  it('keeps demo in loading while DLM migrates', () => {
    expect(
      resolveDesktopLaunchPhase({
        isChecking: false,
        health: {
          ...valid,
          runtime_mode: 'demo',
          status: 'degraded',
          bootstrap_status: 'degraded',
          database_lifecycle_phase: 'migrating',
          migration_pending: true,
        },
        connectionFailed: false,
      }),
    ).toBe('loading')
  })

  it('maps degraded to degraded', () => {
    expect(
      resolveDesktopLaunchPhase({
        isChecking: false,
        health: {
          ...valid,
          status: 'degraded',
          bootstrap_status: 'degraded',
          database_lifecycle_phase: 'ready',
        },
        connectionFailed: false,
      }),
    ).toBe('degraded')
  })

  it('maps health error to error phase', () => {
    expect(
      resolveDesktopLaunchPhase({
        isChecking: false,
        health: {
          ...valid,
          status: 'error',
          bootstrap_status: 'error',
          database_status: 'unavailable',
          database_lifecycle_phase: 'error',
        },
        connectionFailed: false,
      }),
    ).toBe('error')
  })

  it('does not treat degraded as error phase', () => {
    const deg = resolveDesktopLaunchPhase({
      isChecking: false,
      health: {
        ...valid,
        status: 'degraded',
        bootstrap_status: 'degraded',
        database_lifecycle_phase: 'ready',
      },
      connectionFailed: false,
    })
    expect(deg).toBe('degraded')
    expect(deg).not.toBe('error')
  })
})

describe('canProceedWhileDegraded', () => {
  it('allows continue only in development', () => {
    expect(
      canProceedWhileDegraded({
        ...valid,
        status: 'degraded',
        bootstrap_status: 'degraded',
        database_lifecycle_phase: 'initializing',
        migration_pending: true,
      }),
    ).toBe(true)
    expect(
      canProceedWhileDegraded({
        ...valid,
        runtime_mode: 'desktop',
        status: 'degraded',
        bootstrap_status: 'degraded',
        database_lifecycle_phase: 'ready',
      }),
    ).toBe(false)
  })
})

describe('fetchHealthPayload', () => {
  it('returns connectionFailed on network error', async () => {
    vi.stubGlobal('fetch', () => Promise.reject(new Error('network')))
    const r = await fetchHealthPayload('http://example.test/health')
    expect(r.connectionFailed).toBe(true)
    expect(r.health).toBeNull()
    vi.unstubAllGlobals()
  })

  it('returns health on valid 200 JSON', async () => {
    vi.stubGlobal(
      'fetch',
      () =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ ...valid }),
        }) as Promise<Response>,
    )
    const r = await fetchHealthPayload('http://example.test/health')
    expect(r.connectionFailed).toBe(false)
    expect(r.health).toMatchObject(valid)
    vi.unstubAllGlobals()
  })

  it('connectionFailed on non-ok HTTP', async () => {
    vi.stubGlobal(
      'fetch',
      () =>
        Promise.resolve({
          ok: false,
          status: 503,
        }) as Promise<Response>,
    )
    const r = await fetchHealthPayload('http://example.test/health')
    expect(r.connectionFailed).toBe(true)
    vi.unstubAllGlobals()
  })
})
