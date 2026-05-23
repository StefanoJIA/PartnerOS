//! D3: desktop backend sidecar lifecycle (Tauri shell + embedded binary).

use std::sync::Mutex;

use serde::Serialize;
use tauri::{AppHandle, Emitter, Manager, RunEvent};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

/// Default loopback port for the managed FastAPI sidecar (avoid colliding with dev uvicorn on 8000).
pub const DEFAULT_SIDECAR_PORT: u16 = 17_888;

#[derive(Default)]
pub struct SidecarHolder {
  pub inner: Mutex<SidecarInner>,
}

#[derive(Default)]
pub struct SidecarInner {
  pub manage_sidecar: bool,
  pub sidecar_port: u16,
  /// Empty = use Vite dev proxy (`/health` on the dev server origin).
  pub backend_origin: String,
  pub spawn_error: Option<String>,
  pub child: Option<CommandChild>,
}

#[derive(Clone, Serialize)]
pub struct DesktopRuntimeConfig {
  pub backend_origin: String,
  pub manage_sidecar: bool,
  pub sidecar_port: u16,
  pub sidecar_spawn_error: Option<String>,
  pub sidecar_pid: Option<u32>,
}

fn parse_port() -> u16 {
  std::env::var("INTELLIOFFICE_BACKEND_PORT")
    .ok()
    .and_then(|s| s.parse().ok())
    .unwrap_or(DEFAULT_SIDECAR_PORT)
}

/// Path B (product): shell owns the backend process unless opted out.
/// Path A (development): default off in debug builds so `npm run dev` + manual uvicorn keep working.
pub fn should_manage_sidecar() -> bool {
  if std::env::var("INTELLIOFFICE_EXTERNAL_BACKEND")
    .map(|v| v == "1" || v.eq_ignore_ascii_case("true"))
    .unwrap_or(false)
  {
    return false;
  }
  if let Ok(v) = std::env::var("INTELLIOFFICE_MANAGE_SIDECAR") {
    return v == "1" || v.eq_ignore_ascii_case("true");
  }
  !cfg!(debug_assertions)
}

fn dev_backend_origin_when_external() -> String {
  std::env::var("INTELLIOFFICE_DEV_BACKEND_ORIGIN").unwrap_or_default()
}

fn packaged_fallback_backend_origin() -> String {
  std::env::var("INTELLIOFFICE_DEV_BACKEND_ORIGIN")
    .unwrap_or_else(|_| "http://127.0.0.1:8000".to_string())
}

fn spawn_sidecar(app: &AppHandle, port: u16) -> Result<CommandChild, String> {
  let sidecar_path = std::path::Path::new("binaries").join("intellioffice-backend");
  let mut cmd = app
    .shell()
    .sidecar(&sidecar_path)
    .map_err(|e| format!("sidecar command: {e}"))?;

  cmd = cmd
    .env("APP_RUNTIME_MODE", "desktop")
    .env("HOST", "127.0.0.1")
    .env("PORT", port.to_string());

  let (mut rx, child) = cmd.spawn().map_err(|e| format!("sidecar spawn: {e}"))?;

  let app_clone = app.clone();
  tauri::async_runtime::spawn(async move {
    while let Some(event) = rx.recv().await {
      match event {
        CommandEvent::Stdout(line) => {
          log::info!(
            "[sidecar] {}",
            String::from_utf8_lossy(&line).trim_end()
          );
        }
        CommandEvent::Stderr(line) => {
          log::warn!(
            "[sidecar] {}",
            String::from_utf8_lossy(&line).trim_end()
          );
        }
        CommandEvent::Error(e) => log::error!("[sidecar] {e}"),
        CommandEvent::Terminated(status) => {
          log::warn!("[sidecar] terminated: code={:?}", status.code);
          let _ = app_clone.emit("sidecar-exited", status.code);
        }
        _ => {}
      }
    }
  });

  Ok(child)
}

pub fn setup_sidecar(app: &tauri::App) -> Result<(), String> {
  let holder = app.state::<SidecarHolder>();
  let handle = app.handle().clone();
  let mut inner = holder.inner.lock().map_err(|e| e.to_string())?;

  let port = parse_port();
  inner.sidecar_port = port;

  if should_manage_sidecar() {
    inner.manage_sidecar = true;
    inner.backend_origin = format!("http://127.0.0.1:{port}");
    match spawn_sidecar(&handle, port) {
      Ok(child) => {
        inner.child = Some(child);
        inner.spawn_error = None;
      }
      Err(e) => {
        inner.spawn_error = Some(e);
        inner.child = None;
      }
    }
  } else {
    inner.manage_sidecar = false;
    inner.spawn_error = None;
    inner.child = None;
    if cfg!(debug_assertions) {
      inner.backend_origin = dev_backend_origin_when_external();
    } else {
      inner.backend_origin = packaged_fallback_backend_origin();
    }
  }

  Ok(())
}

#[tauri::command]
pub fn get_desktop_config(holder: tauri::State<'_, SidecarHolder>) -> DesktopRuntimeConfig {
  let inner = holder.inner.lock().expect("sidecar mutex poisoned");
  DesktopRuntimeConfig {
    backend_origin: inner.backend_origin.clone(),
    manage_sidecar: inner.manage_sidecar,
    sidecar_port: inner.sidecar_port,
    sidecar_spawn_error: inner.spawn_error.clone(),
    sidecar_pid: inner.child.as_ref().map(|c| c.pid()),
  }
}

pub fn on_run_event(app_handle: &AppHandle, event: &RunEvent) {
  if !matches!(event, RunEvent::Exit) {
    return;
  }
  let maybe_child: Option<CommandChild> = {
    let holder = app_handle.state::<SidecarHolder>();
    let taken = match holder.inner.lock() {
      Ok(mut inner) => inner.child.take(),
      Err(_) => None,
    };
    taken
  };
  if let Some(ch) = maybe_child {
    if let Err(e) = ch.kill() {
      log::warn!("sidecar kill: {e}");
    }
  }
}
