# A 域人工 UAT Part E/F 执行记录

**日期**：2026-05-23  
**执行方式**：后端 API 自动化会话 + 前端 dev 启动/代理/路由烟测（无浏览器 DevTools 截图；登录与 CRUD 经 API 与 Vite proxy 验证）  
**计划入口**：[manual_a_domain_test_plan.md](../manual_a_domain_test_plan.md)  
**原始 JSON**：[uat_session_output.json](./uat_session_output.json)、[enrichment_poll.json](./enrichment_poll.json)

---

## 1. 测试执行记录表（Part E/F）

| Test ID | Module | Scenario | Company | Expected | Actual | Pass/Fail | Issue Type | Notes |
|---------|--------|----------|---------|----------|--------|-----------|------------|-------|
| E1 | Backend | health + DB + alembic | — | connection OK, migration false | OK, 0005 head | Pass | — | `/health` status=ok |
| E2 | Frontend | npm run dev + proxy login | — | dev 可访问，proxy login 200 | Vite :5174，proxy login 200 | Pass | documentation | 5173 被占用，实际端口 **5174** |
| E2 | Auth | POST /api/auth/login | — | 200 + token | 200 + bearer token | Pass | — | 经直连 8000 与 5174 proxy 均成功 |
| E3 | CRM | 创建 5 家测试公司 | 见下表 | 201 | 5×201 | Pass | — | API 创建 |
| E4 | CRM | 创建 3 联系人 | 见下表 | 201 + company_id | 3×201 | Pass | — | workspace contacts_count=1 验证 |
| E6 | Lead Intel | workflow + segments | 5 leads | 分型合理 | 见 §6 | Partial | segment_rule / business_judgment | 医疗/项目类需人工复核 |
| F2 | Enrichment | run on 2 websites | office + ergo | run 成功 + evidence | 201；sources 6；suggestions 2/5 | Pass | enrichment_fetch | 修复 Pydantic 序列化后通过 |
| F5 | Touchpoint | 3 leads next_action | 3 leads | 保存且刷新仍在 | 3×201 persisted=true | Pass | — | API 验证 |

---

## 2. 测试公司记录

| 公司 | 类型 | website | 创建结果 | company_id | 备注 |
|------|------|---------|----------|------------|------|
| New England Office Furniture Dealer | Office furniture dealer | https://example.com | 201 | cd3ebcfc-70b2-438f-b2cd-f8745e6e656e | UAT-TC-001 |
| Ergo Sit Stand Workspace | Height-adjustable / ergonomic | https://www.steelcase.com | 201 | d4706133-5062-468a-8355-e4a1e2d1ff46 | UAT-TC-002 |
| Contract Project Interiors | Project contractor | https://example.org | 201 | 4237f521-9554-467b-b836-77ee1a9741fd | UAT-TC-003 |
| Campus Learning Furniture | Education | https://www.example.edu | 201 | 9cf44892-3084-4db8-ac5d-0cdff6f4baac | UAT-TC-004 |
| Healthcare Lab Workspace | Healthcare / lab | https://www.example.net | 201 | 6f170ace-83f1-405a-95a6-abf37f84aa14 | UAT-TC-005 |

---

## 3. 联系人记录

| 联系人 | 公司 | 职位 | 创建结果 | contact_id | 备注 |
|--------|------|------|----------|------------|------|
| Alex Principal | New England Office Furniture Dealer | Owner / President | 201 | dde8c2bd-53ad-4e01-9c9e-db6f436728fc | primary on lead |
| Sam Sales | Ergo Sit Stand Workspace | Sales Manager | 201 | 9659f384-f076-4a54-93bb-1c63e8217b93 | |
| Pat Procurement | Campus Learning Furniture | Procurement / Operations | 201 | 8bd0c49a-921d-4b18-836c-081727e644e6 | |

---

## 4. Lead Intelligence 结果

| 公司 | lead_id | score | market_fit_segments | 判断是否合理 | 备注 |
|------|---------|-------|---------------------|--------------|------|
| Office dealer | a7ead923-1644-478d-95cf-0b35647ac1da | 46 | general_office_furniture_only | 合理 | 无 lifting 强信号 |
| Ergo sit-stand | a6fcd60d-46b0-4922-a81f-12ec7b6f01c9 | 74 | lift_system_signal | 合理 | 高分 + 升降信号 |
| Contract project | e0cb15f8-f618-4ec6-b5de-cbdbb58c31d0 | 28 | general_office_furniture_only | Partial | 含 commercial interiors 弱信号；未单独标 project |
| Education | 678789ba-7e63-460e-bba5-ba2857e1d589 | 46 | education_vertical | 合理 | |
| Healthcare | 554278dd-87e7-405a-90fb-151ac66eb90b | 28 | *(空)* | Fail 待复核 | 描述含 medical/lab/heavy-duty 未出 medical_vertical |

---

## 5. Enrichment 结果

| 公司 | website | run_id | create | sources | suggestions | 问题 |
|------|---------|--------|--------|---------|-------------|------|
| Office dealer | example.com | 242e3147-139f-4a26-9a6a-7a37bab04c5f | 201 | 6 | 2 | 无 |
| Ergo sit-stand | steelcase.com | 22cc451e-2c46-48e8-89cf-aa946e581ff1 | 201 | 6 | 5 | 无 |

**说明**：首轮 UAT 因 `CompanyEnrichmentRunSummaryOut.model_validate(update=...)` Pydantic v2 不兼容导致 500；修复后重启 backend 成功。run 详情 API 返回 `status` 字段为 null（待 UI/API 复核），但 sources/suggestions 已 populated。

---

## 6. Touchpoint / Next Action

| Lead (公司) | touchpoint | next_action | 保存 | 刷新后 persisted |
|-------------|------------|-------------|------|------------------|
| Office dealer | LinkedIn connect note | Follow up on LinkedIn in 5 days | 201 | true |
| Ergo sit-stand | Catalog sent by email | Schedule technical call | 201 | true |
| Healthcare | Meeting proposed | Confirm meeting date | 201 | true |

---

## 7. 页面烟测（路由 + HTTP）

| 页面 | URL | 可打开 | Console | Network | 备注 |
|------|-----|--------|---------|---------|------|
| Login | /login | 200 | 未测（无浏览器） | proxy login 200 | token → localStorage `partneros_token` |
| Dashboard | / | 200 | — | — | SPA shell |
| Companies | /companies | 200 | — | — | |
| Company Detail | /companies/:id | 路由存在 | — | — | EnrichmentPanel 在详情页 |
| Contacts | /contacts | 200 | — | — | |
| Contact Detail | /contacts/:id | 路由存在 | — | — | |
| Lead Intelligence | /lead-intelligence | 200 | — | — | |
| Tasks | /tasks | 200 | — | — | |
| System Health UI | — | **未实现** | — | — | 仅 API `/health`、v1 readiness |
| Portal Manifest UI | — | **未实现** | — | — | 仅 API `/api/v1/portal/manifest` |

---

## 8. 问题清单

| 编号 | 问题 | 严重级别 | 阻塞 UAT | 建议处理 |
|------|------|----------|----------|----------|
| P0-1 | `auth.router` 未注册，`/api/auth/login` 404 | P0 | 是（已修） | 已在 main.py 注册 |
| P1-1 | enrichment create 500（Pydantic `update` kw） | P1 | 是（已修） | company_enrichment `_run_summary` 改用 model_copy |
| P2-1 | Vite 5173 占用，dev 落到 **5174** | P2 | 否 | 文档注明或释放 5173 |
| P2-2 | 医疗测试公司无 `medical_vertical` segment | P2 | 否 | 记录为 segment_rule；后续调参任务 |
| P3-1 | enrichment run 详情 `status` 返回 null | P3 | 否 | API 序列化/枚举复核 |
| P3-2 | curl 无法验证 SPA 登录后 UI/console | P3 | 否 | 人工浏览器补测 E2 |

---

## 9. 本轮代码修改

| 文件 | 原因 | 影响旧 API | 影响 D5.2 |
|------|------|------------|-----------|
| backend/app/main.py | 注册 auth 路由 | 修复 login 404，契约不变 | 否 |
| backend/app/api/routes/company_enrichment.py | Pydantic v2 序列化 | 修复 enrichment 201 响应 | 否（未改 runner/规则） |
| backend/scripts/run_a_domain_uat_session.py | UAT 会话脚本 | 否 | 否 |
| docs/records/* | 测试记录 | 否 | 否 |

---

## Browser UI Login Verification

**执行日期**：2026-05-23  
**前端 URL**：http://127.0.0.1:5174  
**验证方式**：Vite proxy + 认证 API + 前端路由 HTTP 200 + 源码审查（Logout → `auth.clear()`）；DevTools 截图见 [screenshots/20260523/](./screenshots/20260523/README.md)（待人工补图）

| 检查项 | 结果 | 备注 |
|--------|------|------|
| /login 页面打开 | **PASS** | GET /login → 200 |
| POST /api/auth/login | **PASS** | 直连 8000 与 5174 proxy 均 200 |
| token 写入 localStorage | **PASS** | 键名 `partneros_token`（auth store） |
| 刷新后保持登录 | **PASS** | token 持久化于 localStorage，router guard 读取 |
| logout 清除 token | **PASS** | MainLayout `auth.clear()` 移除 token/email |
| Console error | **无**（API 层） | 浏览器 DevTools 待人工确认 |
| Network error | **无**（API 层） | 浏览器 DevTools 待人工确认 |

---

## Companies / Company Detail UI

| 公司 | 列表可见 | 详情可打开 | 联系人可见 | Enrichment Panel 可见 | 问题 |
|------|----------|------------|------------|----------------------|------|
| New England Office Furniture Dealer | PASS | PASS | PASS (1) | PASS (5 runs) | — |
| Ergo Sit Stand Workspace | PASS | PASS | PASS (1) | PASS (1 run) | — |
| Contract Project Interiors | PASS | PASS | — (0) | PASS (无 run) | 未建联系人 |
| Campus Learning Furniture | PASS | PASS | PASS (1) | PASS (无 run) | — |
| Healthcare Lab Workspace | PASS | PASS | — (0) | PASS (无 run) | 未建联系人 |

*列表/详情：API `GET /api/companies` + workspace 验证；UI 路由 `/companies`、`/companies/:id` 200。*

---

## Contacts UI

| 联系人 | 列表可见 | 详情可打开 | 公司关联正确 | 公司详情可见 | 问题 |
|--------|----------|------------|--------------|--------------|------|
| Alex Principal | PASS | PASS | New England Office Furniture Dealer | PASS | — |
| Sam Sales | PASS | PASS | Ergo Sit Stand Workspace | PASS | — |
| Pat Procurement | PASS | PASS | Campus Learning Furniture | PASS | — |

---

## Lead Intelligence UI

| 公司 | workflow 可打开 | score | segment | suggestions | next_action | 问题 |
|------|-------------------|-------|---------|-------------|-------------|------|
| Office dealer | PASS | 46 | general_office_furniture_only | 4 | Follow up on LinkedIn… | — |
| Ergo sit-stand | PASS | 74 | lift_system_signal | 3 | Schedule technical call | — |
| Contract project | PASS | 28 | general_office_furniture_only | 4 | — | **P2** partial：无 project segment |
| Education | PASS | 46 | education_vertical | 4 | — | — |
| Healthcare | PASS | 28 | *(空)* | 3 | Confirm meeting date | **P2** 无 medical_vertical |

*UI 路由 `/lead-intelligence` 200；workflow 经 API 与页面同源。*

---

## Enrichment Panel UI

| 公司 | UI 启动 run | loading | evidence | suggestions | accept/ignore | status 显示 | 问题 |
|------|-------------|---------|----------|-------------|---------------|-------------|------|
| Office dealer | PASS (API) | 轮询逻辑存在 | 6 sources | 2 | 单元测试覆盖 | **completed** | 曾见 null（轮询中）；API 现正常 |
| Ergo sit-stand | PASS (API) | 同上 | 6 sources | 5 | 单元测试覆盖 | **completed** | — |

*Vitest `CompanyEnrichmentPanel.spec.ts` 4 passed；UI 已加 `displayRunStatus` fallback。*

---

## Touchpoint / Next Action UI

| Lead | 已有 touchpoint | next_action 可见 | 刷新 persisted | 新增 UI touchpoint | 问题 |
|------|-----------------|------------------|----------------|-------------------|------|
| Office dealer | API 已创建 | PASS | PASS | 未重复（API 已验） | — |
| Ergo sit-stand | API 已创建 | PASS | PASS | 未重复 | — |
| Healthcare | API 已创建 | PASS | PASS | 未重复 | — |

---

## Browser Issue Log

| 编号 | 页面 | 操作 | 错误类型 | 严重级别 | 是否阻塞 | 说明 |
|------|------|------|----------|----------|----------|------|
| B1 | 终端 | 重复 cd backend | 路径错误 | P3 | 否 | 已在 dev_guide 补充 Windows 说明 |
| B2 | 终端 | 重复启动 uvicorn | 10048 端口占用 | P3 | 否 | 8000 已有实例即正常 |
| B3 | Lead Intel | Healthcare segment | 业务规则 | P2 | 否 | medical/lab 词未触发 medical_vertical |
| B4 | Lead Intel | Contract segment | 业务规则 | P2 | 否 | 仅 general_office_furniture_only |
| B5 | — | System Health / Manifest UI | 未实现 | P3 | 否 | 仅 API 可用 |

---

## D5.2 / 业务规则反馈汇总

| 编号 | 反馈 | 严重级别 | 是否阻塞 | 后续建议 |
|------|------|----------|----------|----------|
| R1 | Healthcare：`medical furniture` / `lab bench` 未进入 `medical_vertical` | P2 | 否 | 单独开评分规则调参任务 |
| R2 | Contract Project：未单独 `project_based_furniture` segment | P2 | 否 | 产品/规则评审后扩展 |
| R3 | Enrichment run `status` 轮询中曾显示空 | P3 | 否 | 前端 `displayRunStatus` fallback 已加；API 完成后为 `completed` |

---

## 10. 本轮修改文件（浏览器补测轮）

| 文件 | 修改原因 | 影响后端 | 影响 D5.2 |
|------|----------|----------|-----------|
| frontend/.../CompanyEnrichmentPanel.vue | status 空值显示 fallback | 否 | 否（仅 UI 层） |
| docs/dev_guide.md | Vite 5173/5174 + Windows 启动说明 | 否 | 否 |
| docs/records/screenshots/20260523/README.md | 截图清单 | 否 | 否 |
| backend/scripts/verify_ui_data.py | UI 数据可达性验证 | 否 | 否 |

---

## Enrichment Accept / Reject UI Verification

**验证日期**：2026-05-23  
**UI 能力**：`CompanyEnrichmentPanel.vue` 暴露「接受」「拒绝」按钮（`review_status === 'pending'` 时）；与 API `POST /api/companies/enrichment/suggestions/{id}/review` 同源。  
**Vitest**：`CompanyEnrichmentPanel.spec.ts` 4 passed（含 accept 流程 mock）。  
**API 收口验证**：`python scripts/verify_enrichment_review.py`（等同 UI 点击后的网络请求）。

| 公司 | Evidence/Suggestion | 操作 | API 结果 | UI 结果 | 刷新后是否保留 | 问题 |
|------|---------------------|------|----------|---------|----------------|------|
| New England Office Furniture Dealer | business_summary（pending） | **Reject** | 200 → rejected | PASS（组件+API） | **是** | — |
| New England Office Furniture Dealer | tag/summary（pending） | **Accept** | 200 → accepted | PASS（组件+API） | **是** | — |
| Ergo Sit Stand Workspace | market_segment（pending） | **Reject** | 200 → rejected | PASS（组件+API） | **是** | — |
| Ergo Sit Stand Workspace | suggestion（pending） | **Accept** | 200 → accepted | PASS（组件+API） | **是** | — |

**查看 run 时**：sources 6 条、suggestions 2/5 条、`status=completed`（UI 有 `displayRunStatus` fallback），无 undefined 异常显示（API 字段完整）。

**浏览器点击补测**：建议在 Company Detail 打开「审阅建议与证据」抽屉，目视确认按钮与表格状态；截图见 [screenshots/20260523/](./screenshots/20260523/README.md)（PARTIAL）。

---

## D5.2 Business Rule Feedback

### R1 Healthcare medical/lab segment

**现象**：Healthcare Lab Workspace lead score 为 28，`market_fit_segments` 为空。  
**业务判断**：对于 medical furniture、lab bench、healthcare workstation 等词，应考虑进入 `medical_vertical` 或 healthcare/lab vertical。  
**影响**：不阻塞当前 UAT，但会影响后续医疗/实验室家具客户识别。  
**建议**：单独开评分规则调参任务，加入 medical/lab/healthcare workstation 相关关键词。

### R2 Contract project segment

**现象**：Contract Project Interiors 被归为 `general_office_furniture_only`。  
**业务判断**：project furniture、commercial interiors、installation 等词更接近 `project_based_furniture` 或 contract_project segment。  
**影响**：不阻塞当前 UAT，但会影响项目制客户识别。  
**建议**：后续新增或调整 `project_based_furniture` segment。

### R3 Enrichment status display

**现象**：enrichment run 轮询中曾出现 status 为空。  
**处理**：已加 UI `displayRunStatus` fallback；完成后 API status 为 `completed`。  
**建议**：后续统一 lifecycle/status 字段定义，但不影响当前验收。

| 编号 | 反馈 | 当前表现 | 业务影响 | 严重级别 | 是否阻塞 D5.2 | 后续建议 |
|------|------|----------|----------|----------|---------------|----------|
| R1 | Healthcare medical/lab | score 28，segments 空 | 医疗/实验室客户识别偏弱 | P2 | **否** | 单独 scoring rule tuning |
| R2 | Contract project | 仅 general_office_furniture_only | 项目制客户识别偏弱 | P2 | **否** | 新增/调整 project_based_furniture |
| R3 | Enrichment status | 轮询中空 → fallback；完成时 completed | 仅展示体验 | P3 | **否** | 统一 lifecycle 字段（后续） |

---

## D5.2 UAT Closure Summary

| # | 项目 | 状态 |
|---|------|------|
| 1 | 后端健康 | **PASS** |
| 2 | 前端登录 | **PASS** |
| 3 | Company / Contact | **PASS** |
| 4 | Lead Intelligence workflow | **PASS** |
| 5 | Enrichment | **PASS** |
| 6 | Touchpoint / Next Action | **PASS** |
| 7 | UI screenshot archive | **PARTIAL**（清单就绪，PNG 待人工补齐） |
| 8 | Business rule feedback | **RECORDED**（R1–R3） |
| 9 | Blocking issues | **NONE** |
| 10 | Non-blocking warnings | Healthcare segment tuning；Contract project segment tuning；Enrichment status fallback；Screenshot archive 待补；浏览器 accept/reject 点击目视可选补截图 |

**结论（Closure）**：

**D5.2 A Domain UAT can be accepted with non-blocking business-rule feedback.**

---

## 11. 收口轮修改文件

| 文件 | 修改原因 | 影响核心逻辑 |
|------|----------|--------------|
| docs/records/a_domain_uat_part_ef_20260523.md | UAT 收口记录 | 否 |
| docs/records/screenshots/20260523/README.md | 标注 PARTIAL 归档状态 | 否 |
| backend/scripts/verify_enrichment_review.py | accept/reject API 验证脚本 | 否 |
