import { describe, expect, it, vi, beforeEach } from 'vitest'
import type { DesktopRuntimeConfig } from '@/desktop/desktopRuntime'

const { mockInvoke } = vi.hoisted(() => ({
  mockInvoke: vi.fn(),
}))

vi.mock('@tauri-apps/api/core', () => ({
  invoke: mockInvoke,
}))

import { getHealthUrl, resolveDesktopHealthContext } from './backendOrigin'

describe('backendOrigin', () => {
  beforeEach(() => {
    mockInvoke.mockReset()
  })

  it('getHealthUrl uses relative /health when Vite dev default', () => {
    expect(getHealthUrl()).toBe('/health')
  })

  it('resolveDesktopHealthContext maps Tauri config to full health URL', async () => {
    const cfg: DesktopRuntimeConfig = {
      backend_origin: 'http://127.0.0.1:17888',
      manage_sidecar: true,
      sidecar_port: 17888,
      sidecar_spawn_error: null,
      sidecar_pid: 42,
    }
    mockInvoke.mockResolvedValueOnce(cfg)
    const r = await resolveDesktopHealthContext()
    expect(r.healthUrl).toBe('http://127.0.0.1:17888/health')
    expect(r.desktop?.manage_sidecar).toBe(true)
    expect(r.spawnError).toBeNull()
  })

  it('surfaces sidecar_spawn_error from Tauri', async () => {
    const cfg: DesktopRuntimeConfig = {
      backend_origin: 'http://127.0.0.1:17888',
      manage_sidecar: true,
      sidecar_port: 17888,
      sidecar_spawn_error: 'sidecar spawn: not found',
      sidecar_pid: null,
    }
    mockInvoke.mockResolvedValueOnce(cfg)
    const r = await resolveDesktopHealthContext()
    expect(r.spawnError).toBe('sidecar spawn: not found')
  })

  it('falls back when invoke throws (non-Tauri)', async () => {
    mockInvoke.mockRejectedValueOnce(new Error('not in tauri'))
    const r = await resolveDesktopHealthContext()
    expect(r.spawnError).toBeNull()
    expect(r.desktop).toBeNull()
    expect(r.healthUrl).toBe('/health')
  })
})
