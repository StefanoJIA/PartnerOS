/**
 * Backend API origin for desktop shell and health checks (D2/D3).
 * - Vite dev (browser or Tauri + 外部后端): 常为空 → 同源 `/health`、`/api` 由 Vite 代理到 8000。
 * - Tauri + 托管 sidecar: 由 `get_desktop_config` 得到 `http://127.0.0.1:<port>`（默认 17888）。
 */
import type { DesktopRuntimeConfig } from '@/desktop/desktopRuntime'

export function getBackendOrigin(): string {
  const fromEnv = (import.meta.env.VITE_BACKEND_ORIGIN as string | undefined)?.trim()
  if (fromEnv) return fromEnv.replace(/\/$/, '')
  if (import.meta.env.DEV) return ''
  return 'http://127.0.0.1:8000'
}

export function getHealthUrl(): string {
  const o = getBackendOrigin()
  return o ? `${o}/health` : '/health'
}

/** 解析桌面启动所需的 health URL 与 sidecar 状态（浏览器环境下回落到 Vite 规则）。 */
export async function resolveDesktopHealthContext(): Promise<{
  healthUrl: string
  desktop: DesktopRuntimeConfig | null
  spawnError: string | null
}> {
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const cfg = await invoke<DesktopRuntimeConfig>('get_desktop_config')
    if (cfg.sidecar_spawn_error) {
      return {
        healthUrl: '',
        desktop: cfg,
        spawnError: cfg.sidecar_spawn_error,
      }
    }
    const origin = cfg.backend_origin.replace(/\/$/, '')
    const healthUrl = origin ? `${origin}/health` : '/health'
    return { healthUrl, desktop: cfg, spawnError: null }
  } catch {
    // 非 Tauri（浏览器 / Vitest）
  }
  return {
    healthUrl: getHealthUrl(),
    desktop: null,
    spawnError: null,
  }
}

/**
 * 在应用入口调用：Tauri 正式包或托管 sidecar 时把 axios `baseURL` 指到真实后端（`/api` 无 Vite 代理）。
 */
export async function bootDesktopHttpBase(): Promise<void> {
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    const cfg = await invoke<DesktopRuntimeConfig>('get_desktop_config')
    if (cfg.sidecar_spawn_error) return
    const origin = cfg.backend_origin.replace(/\/$/, '')
    if (!origin) return
    const { http } = await import('@/api/http')
    http.defaults.baseURL = `${origin}/api`
  } catch {
    // 非 Tauri或调用失败时保持默认（dev 代理相对路径）
  }
}
