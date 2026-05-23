mod desktop_runtime;

use desktop_runtime::{get_desktop_config, on_run_event, setup_sidecar, SidecarHolder};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .manage(SidecarHolder::default())
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      setup_sidecar(app).map_err(|e| {
        log::error!("desktop_runtime: {e}");
        std::io::Error::new(std::io::ErrorKind::Other, e)
      })?;
      Ok(())
    })
    .invoke_handler(tauri::generate_handler![get_desktop_config])
    .build(tauri::generate_context!())
    .expect("error while building tauri application")
    .run(|app_handle, event| {
      on_run_event(app_handle, &event);
    });
}
