# Open questions — desktop & packaging

以下问题 **尚未最终决议**；记录在案以免阻塞 D0 文档合入。实施 D2–D6 时逐项关闭并回填本页或 ADR。

## 1. Shell 技术栈

- **Tauri 2** 是否覆盖全部需求（单实例、子进程管理、安装器回调、自动更新）？若不行，**Electron** 退路的前提是什么？

## 2. PostgreSQL 托管方式

- **便携捆绑** vs **Windows 服务** vs **首次下载 runtime**：安装包体积、企业策略、杀毒误报、升级方式如何权衡？  
- **pgvector** 与所选 Postgres 发行版的组合是否需自建构建流水线？

## 3. 自动更新

- 代码签名证书、更新通道（内网/公网）、delta 更新失败回滚策略。

## 4. 本地 AI

- 是否在安装包内捆绑 **本地小模型**（体积与合规）？默认仍可能仅 **云端/可配置 API**。

## 5. 云同步（future_cloud）

- 多设备、账号体系、与 desktop local-first 的冲突何时引入；是否与 `future_cloud` 模式绑定。

## 6. 多用户与部署边界

- **单机多 Windows 用户**？**同一局域网多客户端连一台数据服务**？默认 SKU 是否 strictly 单用户单库？

## 7. 许可证与第三方

- Postgres、向量扩展、Tauri/WebView2、PyInstaller 运行时的再分发条款核对（法律评审节点）。

## 8. 桌面数据库载体（PostgreSQL / SQLite / 双路径）

- **D4 实现**绑定本仓库当前 **PostgreSQL + Alembic**；是否在长期产品中保留 **仅 PostgreSQL**、引入 **SQLite** 降级 SKU、或 **双路径**（例如离线演示 vs 完整 pgvector）需经 **正式架构决议** 后改 DLM，不得在迁移策略中隐含切换。

---

**说明**：未决项 **不阻塞** D0–D1 文档与后端 bootstrap 设计；**阻塞** D6 公开发行前检查清单。

## 相关文档

- [packaging_strategy.md](packaging_strategy.md)  
- [database_lifecycle.md](database_lifecycle.md)  
- [roadmap_desktop_transition.md](roadmap_desktop_transition.md)  
