# Packaging strategy（打包与分发策略）

## 1. 目标产物

- **Windows 安装包**（`.msi` / **NSIS** / WiX 等，具体 D6 锁定）。  
- 安装后：**单一桌面快捷方式**「intelliOffice」；双击完成启动链（含本地后端与数据库就绪）。  
- 安装目录或 `%AppData%` 下：**版本号**、日志、配置、（可选）数据库数据目录。

## 2. Desktop shell：Tauri 2 vs Electron

| 维度 | Tauri 2（**当前阶段优先评估**） | Electron |
|------|----------------------------------|----------|
| 运行时体积 | 相对小（系统 WebView） | 捆绑 Chromium，体积较大 |
| 安全面 | Rust 侧壳，攻击面可控 | Node + Chromium，需严格审计 |
| 与 Windows 集成 |  Tray、单实例、安装体验较好 | 成熟生态、案例多 |
| 团队曲线 | 需 Rust 与前端协作 | 偏 JavaScript 全栈 |

**建议**：**D2** 原型以 **Tauri 2** 为主路径；若在 **启动子进程、IPC、安装器** 上遇阻，再评估 Electron 作为备选，并在文档与 [open_questions_desktop.md](open_questions_desktop.md) 中记录决策。

**D2 已落地（仓库事实）**：`frontend/src-tauri` 为 Tauri 2 最小工程；`tauri dev` / `tauri build` 依赖本机 **Rust** 工具链。

**D3 已落地（Windows 最小链路，仓库事实）**：

- **Sidecar 可执行文件**：PyInstaller 单文件 **`intellioffice-backend.exe`**（由 `sidecar_entry.py` 启动 Uvicorn）；构建命令 **`cd frontend && npm run sidecar:prepare`**（详见 [testing.md](testing.md) D3）。  
- **Tauri 集成**：`tauri.conf.json` → `bundle.externalBin`: `["binaries/intellioffice-backend"]`；运行时由 **`tauri-plugin-shell`** 以 sidecar 方式 `spawn`，注入 **`APP_RUNTIME_MODE=desktop`**、`HOST`、`PORT`；应用退出时 **`RunEvent::Exit`** 上对已持有子进程 **`kill`**。  
- **能力**：`capabilities/default.json` 中 `shell:allow-spawn` 允许 `binaries/intellioffice-backend`（`sidecar: true`）。  
- **仍属后续**：安装包签名、自动更新、**macOS/Linux** sidecar 与 triple 验收、非 Windows 打包流水线。

## 3. 后端 sidecar（FastAPI）

- **形式（D3）**：**PyInstaller** 将 **`sidecar_entry.py`** 打成 **`intellioffice-backend.exe`**，由 **Tauri shell** 按 `externalBin` 约定启动，默认监听 **`127.0.0.1:17888`**（与开发用 8000 错开；详见 `desktop_runtime.rs` 与 [testing.md](testing.md)）。占位后 D4+ 可评估占用检测或递增端口。  
- **契约**：健康检查 `GET /health`（D1 JSON）；壳在启动后 **轮询** health直至可判定 **ready / degraded / error**。  
- **前端**：Tauri 装载 `vite build` 产物；**无 Vite 代理** 时由 `bootDesktopHttpBase()`（`backendOrigin.ts`）在启动时将 axios `baseURL` 设为 **`<backend_origin>/api`**。开发期浏览器 / `tauri dev` + 外部后端仍用 **`npm run dev`** 代理 `/api` 与 `/health`。

## 4. PostgreSQL 托管路径（选项，未最终锁定）

1. **捆绑便携式 Postgres**（pgvector 构建或官方二进制 + 扩展）：安装包解压到应用目录，DLM 负责 `initdb`、启停。  
2. **安装阶段注册 Windows 服务**（企业感强，权限与升级复杂）。  
3. **首次运行下载 runtime**（减小安装包，需网络与校验）。  

详尽对比与法务/体积约束记在 [open_questions_desktop.md](open_questions_desktop.md)；**不阻塞 D0–D3** 的 Windows shell + sidecar 串联（macOS/Linux 仍属后续）。

## 5. 自动更新（D6）

- Tauri 内置 updater 或 Squirrel / 自建 CDN；**签名证书**、delta 包、回滚策略后续单独立项。

## 6. 相关文档

- [architecture_desktop_target.md](architecture_desktop_target.md)  
- [database_lifecycle.md](database_lifecycle.md)  
- [migration_from_web_to_desktop.md](migration_from_web_to_desktop.md)  
