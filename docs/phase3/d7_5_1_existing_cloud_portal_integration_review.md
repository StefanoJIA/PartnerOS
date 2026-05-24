# D7.5.1 Existing Cloud Portal Integration Review

**Status:** Review complete · **Date:** 2026-05-24 · **Alembic head:** `0013_prod_milestones` (unchanged)

## 1. Goal

审查已上线 **HOSUN & intelli 云端客户系统** 与当前 **PartnerOS (intelliOffice)** 仓库的关系，判断集成路线，避免重复开发或推倒重做。

本阶段 **仅审查与文档**，不实现 Portal API、不部署云端、不改 schema。

---

## 2. Existing Cloud Portal Capabilities

根据用户补充与仓库内线索，已上线云端客户系统（部署于云端服务器，域名可能为 `service.intelli-opus.com` 或同类）大致包含：

| 能力 | 说明 | 仓库内直接证据 |
|---|---|---|
| **Product selection** | 客户浏览 / 选购商品 | 无云端 Portal 源码；PartnerOS 有 `product_catalog` 作为内部目录 |
| **Logistics / order tracking** | 客户查看订单 / 物流状态 | 无云端 tracking 模块源码；PartnerOS 尚无 `shipment_plans`（D7.6） |
| **Feedback** | 客户意见反馈 | 无 Portal feedback 表；PartnerOS 仅有 **Sample** 级 `customer_feedback`（`/api/samples/{id}/feedback`） |
| **Resource download** | 客户资料 / 文档下载 | 无独立 document center；PartnerOS 有 `quote_pdf_exports`、`ProductDocument`、本地 storage |
| **Customer account / access** | 登录与权限 | 无 SSO 实现；`integrated_backend_standards.md` 规划 Phase 5 Portal SSO |

**仓库检索结论：**

- **未找到** `service.intelli-opus.com` 配置或云端 Portal 前端/后端源码。
- **已找到** PartnerOS 侧 **D5.2 Portal 只读集成**（面向 **内部/统一 Portal**，非客户订单 Portal）：
  - `GET /api/v1/portal/manifest`
  - `GET /api/v1/portal/summary`（lead intelligence 摘要）
  - `GET /api/v1/portal/a-domain/status`
- **已找到** 前端 mock：`/portal-consumer-mock`（`PortalConsumerMockPage.vue`）
- **已找到** 部署文档：`docs/records/d5_2_9_portal_readonly_integration_20260523.md`、`d5_2_10_portal_consumer_deployment_readiness_20260523.md`

云端客户系统 **不在本仓库**，应视为 **已部署的外部 Consumer**，需通过 API 桥接而非在本仓库重写 UI。

---

## 3. Current PartnerOS Capabilities

| 域 | 已实现 | 表 / API 要点 |
|---|---|---|
| **Product catalog** | ✅ D6 | `product_catalog`, `GET /api/v1/products` |
| **Quote** | ✅ D6 | `quotes`, PDF export, send tracking, order-readiness |
| **Customer order** | ✅ D7.2 | `customer_orders`, `order_line_items` |
| **Customer confirmation** | ✅ D7.3 | `order_confirmations` |
| **Partner split** | ✅ D7.4 | `order_partner_splits` |
| **Supplier confirmation** | ✅ D7.4 | `supplier_confirmations` |
| **Production milestones** | ✅ D7.5 | `order_production_milestones` |
| **Shipment tracking** | ❌ D7.6 | `shipment_plans` 仅设计，未 migration |
| **Customer portal API** | ❌ D7.7 | roadmap 标注 Future |
| **Feedback tickets** | ❌ D7.8 | 未实现 |
| **Resource center** | ❌ D7.9 | 未实现 |

内部 Operator UI：`/orders`, `/quotes`, `/products` 等。

---

## 4. Mapping Table

| Cloud Portal Capability | PartnerOS Source of Truth | Integration Direction |
|---|---|---|
| **商品选购** | `product_catalog`, `product_price_tiers` | Portal **只读**拉取已发布 SKU；不下单写库；价格以 **已发送 Quote** 为准 |
| **报价 / 价格展示** | `quotes`, `quote_line_items`, `quote_pdf_exports` | 客户侧仅展示 **已确认 Quote PDF / 摘要**；不暴露 margin / cost |
| **订单追踪** | `customer_orders`, `order_confirmations` | Portal 读 `order_number`, `status`, 客户可见 line items |
| **生产进度** | `order_production_milestones` | Portal 读 milestone label / status；**不**暴露 supplier notes |
| **物流追踪** | future `shipment_plans`, `tracking_events` (D7.6) | Portal 读 ETD/ETA/tracking；PartnerOS 人工维护 |
| **意见反馈** | future `feedback_tickets` (D7.8) | Portal POST → PartnerOS 工单；可关联 `customer_orders.id` |
| **文件下载** | `quote_pdf_exports`, future document center (D7.9) | Portal 签名 URL 下载；文件存 `backend/storage/`（gitignore） |
| **客户账户** | future Portal auth bridge | SSO / token；PartnerOS 不存 Portal 密码 |
| **Lead / 销售情报** | 现有 `GET /api/v1/portal/summary` | **保持内部**；不混入客户 Portal |

---

## 5. Recommended Architecture

```
┌─────────────────────────────────────┐
│   PartnerOS Internal Backend        │
│   (Quote / Order / Production /     │
│    Shipment source of truth)        │
└──────────────┬──────────────────────┘
               │  internal APIs
               ▼
┌─────────────────────────────────────┐
│   Portal API Layer (future D7.7)    │
│   /api/v1/portal/customer/*         │
│   - field filtering                 │
│   - customer-scoped auth            │
│   - no internal cost/margin         │
└──────────────┬──────────────────────┘
               │  HTTPS + token
               ▼
┌─────────────────────────────────────┐
│   Existing Cloud Customer Portal    │
│   (HOSUN & intelli, already live)   │
│   - product selection UI            │
│   - order / logistics tracking UI   │
│   - feedback UI                     │
│   - resource download UI            │
└─────────────────────────────────────┘
```

**原则：**

1. **保留** 已上线云端 Portal 作为 **客户侧唯一入口**（不重做 UI）。
2. **PartnerOS** 作为 **业务 source of truth**（订单、生产、物流、文档元数据）。
3. Portal **只展示客户可见字段**；禁止暴露 supplier confirmation 细节、margin、internal notes。
4. D5.2 现有 `/api/v1/portal/summary` 继续服务 **内部 lead intelligence**，与客户 Portal **分域**。

---

## 6. API Boundary Proposal

以下 API **本阶段仅设计**，D7.7 实现：

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/portal/customer/products` | 客户可见产品列表 |
| GET | `/api/v1/portal/customer/orders` | 当前客户订单列表 |
| GET | `/api/v1/portal/customer/orders/{id}/status` | 订单状态摘要 |
| GET | `/api/v1/portal/customer/orders/{id}/production` | 生产里程碑（过滤字段） |
| GET | `/api/v1/portal/customer/orders/{id}/shipment` | 物流状态（D7.6 后） |
| POST | `/api/v1/portal/customer/feedback` | 提交反馈工单 |
| GET | `/api/v1/portal/customer/resources` | 可下载资源列表 |

**Response 必须包含 safety flags：**

- `shipment_created`, `supplier_notified`, `customer_notified`, `automatic_sending_enabled` → false（除非业务真实且客户可见）
- 禁止返回 internal cost, margin, supplier_reference, voided confirmations

---

## 7. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| 两套系统数据重复 | 订单状态不一致 | PartnerOS 为唯一写源；Portal 只读 + 缓存 TTL |
| 云端 Portal 与 PartnerOS 状态不同步 | 客户看到过期信息 | Webhook 或轮询 + `updated_at` 版本 |
| 客户侧暴露 internal 信息 | 合规 / 信任风险 | Portal API 字段白名单；独立 DTO |
| 物流状态人工维护成本 | 追踪延迟 | D7.6 shipment_plans + operator UI |
| Feedback 无回流 | 客户声音丢失 | D7.8 feedback_tickets 写入 PartnerOS |
| 权限与 token 风险 | 越权访问 | 客户 scoped JWT；独立 portal auth |
| 云端域名 / 部署不在仓库 | 集成文档漂移 | 运维 runbook + manifest 登记 `PUBLIC_BASE_URL` |
| 与 D5.2 internal portal 混淆 | 错误 API 消费 | 路径分域：`/portal/summary` vs `/portal/customer/*` |

---

## 8. Next Development Recommendation

推荐顺序（在 **不替换** 云端 Portal 前提下）：

| Stage | Name | Scope |
|---|---|---|
| **D7.6** | Shipment Tracking Foundation | `shipment_plans`, tracking events, operator 维护 |
| **D7.7** | Customer Portal Bridge | `/api/v1/portal/customer/*` 读 API + auth |
| **D7.8** | Feedback / Ticketing | `feedback_tickets`, Portal POST 回流 |
| **D7.9** | Resource Center | 客户文档 catalog + 签名下载 |
| **D8** | Deployment & Integration Hardening | CORS, HTTPS, token rotation, 云端联调 |

**不建议：** 在本仓库重建完整客户 Portal UI 或废弃已上线云端系统。

---

## 9. Final Judgment

**A. Existing cloud portal should be retained as customer-facing portal and integrated with PartnerOS as source of truth.**

理由：

1. 云端系统已部署且具备完整客户能力（选购、追踪、反馈、下载）。
2. PartnerOS 已具备 order → production 内部链路，缺 shipment + portal bridge。
3. 仓库已有 Portal 集成模式（manifest / envelope / consumer mock）可扩展为客户域。
4. 替换云端 Portal 成本高、风险大，且无仓库源码支持重写。
5. 集成路径清晰：D7.6 → D7.7 → D7.8 → D7.9 → D8。

---

## Appendix: Repository Search Hits

| Keyword | Finding |
|---|---|
| `portal` | D5.2 v1 routes, portal_integration service, smoke scripts |
| `customer portal` | D7.1/D7.7 design docs only |
| `service.intelli-opus.com` | **Not found** in repo |
| `HOSUN` | Partner seed data, docs; not cloud portal code |
| `tracking` | Quote send tracking (D6.5); order production; no shipment |
| `feedback` | Sample feedback API only |
| `product_catalog` | D6 implemented |
| `cloud` | `future_cloud` runtime mode, deployment docs |
