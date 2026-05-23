/**
 * Mirrors Rust `DesktopRuntimeConfig` (snake_case JSON from Tauri).
 * @see frontend/src-tauri/src/desktop_runtime.rs
 */
export interface DesktopRuntimeConfig {
  backend_origin: string
  manage_sidecar: boolean
  sidecar_port: number
  sidecar_spawn_error: string | null
  sidecar_pid: number | null
}
