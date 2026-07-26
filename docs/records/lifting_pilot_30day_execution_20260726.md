# PartnerOS 升降系统 30 天试点执行计划

**Agent:** D — Lifting Systems 30-Day Pilot Plan  
**Date:** 2026-07-26  
**Scope:** Desk Frames · Desk Legs · Lifting Columns（HOSUN lifting systems）  
**Mode:** 只读分析 + 执行记录（本文档）；**未改代码、未发布**  
**Runtime state:** `READY_FOR_STAGING_HANDOFF` · `WAITING_FOR_REAL_STAGING_EVIDENCE`  
**Explicitly NOT claimed:** `STAGING_VALIDATED` · D9 entered · real business owner sign-off · real HOSUN field approval

---

## 0. 文档用途与边界

本计划将 **desk frames / desk legs / lifting columns** 三类 SKU 的 Market Response 试点，压缩为 **30 天可控闭环**：

```text
真实 lead / 反馈 → 能力回填 → interval quote → quote learning → Market Response review
```

**安全边界（与代码一致）：**

- `market_response_safety()` / `QUOTE_LEARNING_SAFETY`：只读聚合、建议性输出、人工审查；不自动改 quote/order、不自动通知客户/供应商。
- D8.26 field review：load / noise / stability / cert / warranty **全部为 pending**；unsupported = **pilot blocker**。
- Catalog `heavy_duty_rule` 推断 300kg 带 `needs_business_validation`——**不得**作为已批准对外承诺。

**关联代码锚点：**

| 模块 | 路径 |
|---|---|
| Lifting project expectations | `backend/app/services/market_response_intelligence.py` → `build_lifting_project_expectations()` |
| Capability schema | `backend/app/services/product_capability_schema.py` → `LIFTING_CAPABILITY_FIELDS` / `PROJECT_REQUIREMENT_SIGNALS` |
| Quote learning 升档 | `backend/app/services/quotes/quote_learning.py` → `promote_quote_learning_to_market_response()` |
| Daily queue HOSUN 强制项 | `backend/app/services/daily_decision_queue.py` → `_select_operating_items()` |
| Market Response 种子 | `backend/app/services/market_response_reviews.py` → `DEFAULT_REVIEWS` |
| 300kg 命名推断 | `backend/app/services/quotes/catalog_enrichment.py` → `HEAVY_DUTY_LOAD_KG` / `heavy_duty_rule` |
| Field review 门槛 | `docs/phase3/d8_26_hosun_lifting_systems_field_review.md` |

---

## 1. 信号分类：真实 vs 假设 vs Demo

| 类型 | 标识 | 来源 | 内容摘要 | 试点可用性 |
|---|---|---|---|---|
| **真实客户信号** | `REAL` | D5.2.6 / D5.16 UAT batch（`local_data/*.private.csv`，不提交） | SWC、HAT、OCI、Yony's、Jefferson、Dancker 等；segment 规则：`lift_system_signal` / `project_based_furniture` / OEM | **可用作 outreach 对象**；非成交/丢单统计 |
| **真实客户信号** | `REAL` | D5.19 soft quote handoff UAT | SWC / Yony's / OCI → HOSUN lifting；missing qty/timeline/color | **可用作 quote readiness 缺口证据** |
| **内部假设 / 运营模板** | `ASSUMPTION` | `DEFAULT_REVIEWS` | load P1 needs validation；noise P1 needs validation；delivery P2 watching | **方向提示**，非市场结论 |
| **内部假设 / 规则引擎** | `ASSUMPTION` | D5.17 lifting rule tuning | heavy-duty / OEM / project_supply 加权；discovery ≤4 问 | **产品策略**，非客户原话 |
| **Catalog / 命名推断** | `ASSUMPTION` | `catalog_enrichment.heavy_duty_rule` | 品名含 300kg/heavy-duty → 300kg；3-leg → 360kg；dual-motor → 120kg | **须 HOSUN 实测/文档确认** |
| **Schema 评分规则** | `ASSUMPTION` | `evaluate_project_requirement_fit()` | ≥120kg = strong；noise ≤50dB = strong | **内部 fit 逻辑**，非认证 |
| **Demo / 测试合成** | `DEMO` | `test_market_response_intelligence.py` 等 | "Delayed adjustable frame shipment"；"Buyers ask for lower noise and BIFMA"；certification lost reason | **禁止**作市场证据 |
| **待外部输入** | `PENDING` | D8.26 / D8.33 tracker | HOSUN load/noise/cert/test cycle 材料 | **未收到** → stays `needs validation` |

**结论：** 当前 **无足够真实 win/loss / feedback 密度** 支撑单一 go-to-market 结论。30 天试点目标是 **产生新证据**，而非放大 demo 或命名推断。

---

## 2. P0 试点项（30 天内必须推进 — 阻塞解除）

> P0 = 不解除则无法安全发出 customer-facing quote 或 controlled pilot claims。

### P0-1 · 300kg / 660lb 重载能力

| 字段 | 内容 |
|---|---|
| **市场证据** | `REAL`：D5.16 SWC（dealer/lift）、HAT（OEM/lift）product focus = HOSUN lifting；product fit 对 lifting lead 常缺 `load_capacity_requirement`（D5.19）。`ASSUMPTION`：D5.17 `heavy_duty_fit` 加权；`catalog_enrichment` 识别 300kg 关键词。 |
| **当前能力** | Portal compat 有 `heavy-duty` 筛选；fit 规则 ≥120kg → strong_fit；enrichment 推断 300kg/661lb（`needs_business_validation`）。`attributes_json.load_capacity_kg` **多数未结构化**。 |
| **未验证假设** | ① 命名 300kg = 实测 300kg；② SWC/HAT 当前项目确需 ≥120kg；③ HRD SKU 可 interval quote 无 engineering exception。 |
| **目标客户类型** | 工业/workbench 经销商（SWC 类）；heavy-duty OEM 组件商（HAT 类）；项目家具商（Jefferson/Dancker 类 heavy project）。 |
| **样品 / 测试方法** | ① 向 HOSUN 索取 **load test summary**（非 raw notes，D8.26）；② 选 1 款 HRD/300kg 代表 SKU 做 internal interval quote rehearsal；③ quote learning 记录 load 维度 win/loss/objection。 |
| **成功指标** | 30 天内：≥1 份 heavy-duty draft quote；load Market Response review → `reviewed` + approved customer-safe range（至少 standard + heavy 两档）；`build_lifting_project_expectations` heavy_load avg score ≥55。 |
| **Owner · 时间线** | Business owner + HOSUN · **Week 1–2** 材料请求；**Week 2** wording 审查；**Week 3** quote 发出 |
| **工程审查** | **Y** |

### P0-2 · 噪音 / 振动（Noise）

| 字段 | 内容 |
|---|---|
| **市场证据** | `ASSUMPTION`：`DEFAULT_REVIEWS` noise P1（lifting columns）；`NEGATIVE_TERMS` 含 `noise`；quote learning 11 维含 noise，lost + noise → P1。`DEMO`：测试数据 "Buyers ask for lower noise and BIFMA" — **不可引用为真实客户**。 |
| **当前能力** | Schema 有 `noise_db`；quiet ≤50dB → fit score 88；market gap 检测 `noise_level` 缺失；lifting columns focus category 已映射。 |
| **未验证假设** | ① 目标 segment 对 dB 阈值有统一要求；② HOSUN 可提供 test cycle summary；③ 视频/样品测噪可与 lab 数据对齐。 |
| **目标客户类型** | 开放办公 project buyer；医疗/高端 corporate（**不对外声称 medical approval**）；conference/workstation 集成商。 |
| **样品 / 测试方法** | HOSUN test cycle summary + 竞品 dB 区间对照；1 次 internal 样品或视频测噪（记录 internal-only）；promote quote learning → noise review。 |
| **成功指标** | noise review：`needs validation` → `reviewed`；≥2 条 quote learning 含 noise 因素；top 5 frame SKU 有 `noise_db` 或 explicit "pending test" 标记。 |
| **Owner · 时间线** | Product / business owner + HOSUN · **Week 1** 材料；**Week 2–3** 审查闭环 |
| **工程审查** | **Y** |

### P0-3 · 横向 / 前后稳定性（Lateral / Front-Back Stability）

| 字段 | 内容 |
|---|---|
| **市场证据** | `ASSUMPTION`：D8.26 stability = sensitive + pilot blocker if unsupported；`high_stability` requirement signal；quote learning 维度含 stability。`DEMO`：win-loss 测试中 stability 为 winning factor — **仅开发参考**。 |
| **当前能力** | `stability_rating` 字段存在；fit 有 `high_stability` signal；**无** lateral vs front-back 拆分；**无** rating 枚举/测试方法入库。 |
| **未验证假设** | ① 超宽桌面 wobble 是首要 objection；② desk frame vs leg-only 稳定性可共用 summary；③ 1 份 questionnaire 可代表 project segment。 |
| **目标客户类型** | 大桌面 project buyer；conference / benching 集成商（Jefferson/Dancker 类）；multi-leg workstation  specifier。 |
| **样品 / 测试方法** | HOSUN stability test summary（wobble / load offset）；frame vs leg 分开描述；1 个 ultra-wide 场景 internal questionnaire（≤4 问，D5.17）。 |
| **成功指标** | stability 进入 ≥1 份 `customer-safe candidate` 草稿；project expectation `high_stability` fit ≥55；≥1 quote learning 记录 stability 因素。 |
| **Owner · 时间线** | Business owner + engineering liaison · **Week 2** test summary；**Week 3** wording |
| **工程审查** | **Y** |

### P0-4 · 超宽 / 多腿 / 会议桌（Ultra-Wide / Multi-Leg / Conference）

| 字段 | 内容 |
|---|---|
| **市场证据** | `ASSUMPTION`：`extra_wide_multi_leg` signal → `width_range_mm`；catalog enrichment 3-leg → 360kg、benching 4-leg 推断；margin tier 对 triple/4-motor 升 profit。`REAL`：Jefferson/Dancker → `project_based_furniture`（project supply，非专指 conference）。 |
| **当前能力** | `width_range_mm`、`leg_count` 推断逻辑存在；combination workstation load 分侧计算；**width_range_mm 普遍缺失**；conference 无独立 SKU 治理；multi-leg 同步/控制未建模。 |
| **未验证假设** | ① 3-leg SKU 代表当前 project 需求；② 360kg 推断可 quote；③ L-shape / conference 可共用 1 份 quote 模板。 |
| **目标客户类型** | Project furniture 商（Jefferson/Dancker）；corporate AV/conference 集成商；dealer 大单 benching。 |
| **样品 / 测试方法** | 选 1 个 3-leg / L-shape 代表 SKU；回填 width + leg_count + controller；做 1 份 project interval quote draft；engineering review multi-leg sync。 |
| **成功指标** | ≥1 multi-leg project quote draft；≥3 SKU 有 `width_range_mm` + leg_count；daily queue 无 load pilot blocker on selected SKU。 |
| **Owner · 时间线** | Product ops + sales · **Week 2** SKU 选定；**Week 2–3** quote draft |
| **工程审查** | **Y** |

### P0-5 · 样品路径 + 客户反馈闭环（Samples + Customer Feedback）

| 字段 | 内容 |
|---|---|
| **市场证据** | `ASSUMPTION`：`sample_validation` signal → MOQ；gap 字段 `sample_available`；D5.14 pre-quote sample prep kit workflow。`REAL`：D5.16 多数 pilot lead 为 almost_ready / not_ready，missing info 常含 color/cert/delivery（**非样品已请求证据**）。 |
| **当前能力** | Pre-quote sample brief 可用；MOQ 字段关联 sample signal；**sample_available 未批量填充**；样品 lead time / 费用未入 quote 逻辑。 |
| **未验证假设** | ① 样品是 dealer 决策必要条件；② 1–2 款 frame sample SKU 可覆盖 80% discovery；③ feedback ticket 可在 30 天内产生 lifting 信号。 |
| **目标客户类型** | 新 dealer（SWC/OCI 类）；project spec 阶段 buyer（Yony's/Jefferson 类）；OEM 评估样品（HAT 类 — 可能偏 column/controller）。 |
| **样品 / 测试方法** | 定义 frame + leg 各 1 款 sample SKU + 内部审批流程；1 次 internal 样品询价 rehearsal（D5.14 workflow）；feedback ticket 与 quote learning 双向链接。 |
| **成功指标** | ≥2 SKU `sample_available=true`；≥1 sample 请求进入 quote draft 或 external execution action；lifting feedback signal count ≥1（**单条不作结论**，见 `single_feedback_is_not_conclusion`）。 |
| **Owner · 时间线** | Operator + product ops · **Week 1** SKU 定义；**Week 3–4** rehearsal + feedback 收集 |
| **工程审查** | **N**（流程/商务为主；frame 结构问题升 engineering） |

---

## 3. P1 试点项（核心扩展 — Week 2–4 并行）

> P1 = 30 天内启动 discovery / 数据回填 / review 闭环；不要求全部 customer-visible。

### P1-1 · 医疗 / 工业集成（Medical / Industrial Integration）

| 字段 | 内容 |
|---|---|
| **市场证据** | `REAL`：D5.16 Metro Lab Workspace Co → medical/lab segment（UAT 样本）。`ASSUMPTION`：product fit `medical_vertical` + lifting → stability/load/cert 缺失检测；PRD 提及 medical/lab workspace。 |
| **当前能力** | `medical_industrial` → certifications signal；segment enum 含 medical furniture manufacturer；**无** UL/IEC/医疗级 cert 结构化数据；工业集成（mounting/e-stop）未在 schema。 |
| **未验证假设** | ① 30 天内有 medical lead 可跟进；② HOSUN 有任一 cert 可映射；③ industrial = heavy-duty 可合并 pitch。 |
| **目标客户类型** | HAT 类 OEM；medical workstation 集成商（**需资质，不对外声称 medical approval**）。 |
| **样品 / 测试方法** | Cert 需求 questionnaire（不承诺）；HOSUN cert summary 索引；若有 medical lead → 定向 discovery ≤4 问。 |
| **成功指标** | cert requirement 录入 ≥2 leads；certification review 有 `evidence_summary`；**零**对外 medical/industrial compliance 声明。 |
| **Owner · 时间线** | Business owner · **Week 2–4** discovery |
| **工程审查** | **Y** |

### P1-2 · 安装孔位 + 控制器定制（Mounting Holes + Controller Customization）

| 字段 | 内容 |
|---|---|
| **市场证据** | `REAL`：HAT → OEM/lift component focus（D5.16）。`ASSUMPTION`：`custom_mount_holes` → `custom_engineering` boolean；OEM fit 问 customization；HOSUN PRD 含 hand controls。 |
| **当前能力** | Schema 有 `custom_engineering`、`controller_type`；**无** hole pattern / CAD 字段；控制器 SKU 与 frame 捆绑规则未治理；Portal 客户可见性未审。 |
| **未验证假设** | ① HAT 当前询价含 custom hole pattern；② controller compatibility 可手工 matrix 维护；③ branded controller 有 MOQ。 |
| **目标客户类型** | OEM/ODM component buyers（HAT）；dealer 标准 SKU + 可选 handset upgrade。 |
| **样品 / 测试方法** | OEM 询价模板（孔位图 + MOQ，internal）；controller compatibility matrix（frame ↔ handset/memory）；sample kit 流程 rehearsal。 |
| **成功指标** | ≥1 OEM discovery 完成；`custom_engineering=true` 入库 ≥2 SKU；controller_type 覆盖 ≥80% active frames。 |
| **Owner · 时间线** | Product ops + HOSUN engineering liaison · **Week 2–3** matrix；**Week 4** OEM template |
| **工程审查** | **Y** |

### P1-3 · 粉末涂装 / 颜色 / 组装质量（Powder Coat / Color / Assembly Quality）

| 字段 | 内容 |
|---|---|
| **市场证据** | `REAL`：D5.19 missing info 常含 color/finish（SWC/Yony's/OCI）。`ASSUMPTION`：HOSUN color swatch sample set（PRD）；product fit 缺 `color_or_finish`。 |
| **当前能力** | `finish_options` list 字段；orders_domain 枚举含 Powder Coating；**Catalog finish 未系统化**；MOQ/lead time 按色未关联。 |
| **未验证假设** | ① 标准色板 5–8 色可覆盖 90% dealer 需求；② 定制色 MOQ 可接受；③ 组装质量可通过样品而非 solely spec sheet 验证。 |
| **目标客户类型** | Project buyer 需品牌色（Jefferson/Dancker）；dealer 标准黑/白/灰（SWC/OCI/LABERS）。 |
| **样品 / 测试方法** | 导入标准色板 + MOQ 表；1 次 swatch sample 请求 internal rehearsal（D5.14）；quote terms 注明 finish MOQ（editable，非 auto-send）。 |
| **成功指标** | ≥5 frame SKU 有 `finish_options`；`sample_validation` signal fit ≥75 on ≥1 SKU；≥1 quote draft 含 finish 区间说明。 |
| **Owner · 时间线** | Product ops · **Week 2** 色板；**Week 3–4** sample rehearsal |
| **工程审查** | **N**（商务/供应链为主；结构组装问题升 Y） |

### P1-4 · 认证 / 保修 / 交期（Certifications / Warranty / Lead Time）

| 字段 | 内容 |
|---|---|
| **市场证据** | `ASSUMPTION`：`DEFAULT_REVIEWS` load P1；desk legs delivery P2；quote learning lost + certification → P1；D8.26 cert/warranty = pilot blocker if unsupported。`DEMO`：测试 lost reason = certification — **不可作真实丢单率**。 |
| **当前能力** | `certifications` list + `certification_required` / `lead_time_sensitive` signals；`lead_time_days`、`warranty` 字段存在；**产品级 cert 几乎空白**；customer-visible delivery window 未批准。 |
| **未验证假设** | ① UL/CE 覆盖 top 10 SKU；② 标准 lead time 可统一表述；③ warranty 可在不暴露 cost exposure 前提下 customer-safe。 |
| **目标客户类型** | 需合规 corporate project；有时间窗的 project buyer；dealer 关心 warranty + lead time（OCI/SWC 类）。 |
| **样品 / 测试方法** | HOSUN cert pack 索引 → 逐 SKU 映射；标准 vs 定制 lead time 表；1 单 delivery review + 1 单 warranty wording draft（D8.26 矩阵）。 |
| **成功指标** | Top 10 frame SKU 有 cert list 或 explicit pending；≥1 cert review → `reviewed`；`lead_time_days` 覆盖 top 10 SKU；delivery review → `customer-safe candidate` 草稿。 |
| **Owner · 时间线** | Business owner + operator · **Week 1–2** cert index；**Week 3–4** lead time / warranty wording |
| **工程审查** | **Y**（cert/test cycle）；**N**（lead time 计划/物流） |

---

## 4. P2 试点项（30 天后或低资源并行）

| ID | 项 | 理由 | Owner | 工程审查 |
|---|---|---|---|---|
| P2-1 | Desk legs 独立组件 quote 路径 | Frame 试点稳定后再拆 leg-only SKU | Product ops | Y（load/stability） |
| P2-2 | Lifting columns OEM 组件 brief | HAT 类 column/controller 深度 discovery | Sales + engineering | Y |
| P2-3 | `lifting-project-expectations` API 接入 Commercial Intelligence UI | 系统可视化；不阻塞业务试点 | Engineering | N |
| P2-4 | Portal heavy-duty 浏览 staging rehearsal | 需 staging credentials + P0 load wording | Ops | Y |
| P2-5 | Medical/industrial cert 深度包 | P1-1 discovery 有结果后再展开 | Business owner | Y |
| P2-6 | Multi-leg 同步控制专项 | P0-4 quote 暴露需求后再立项 | Engineering | Y |
| P2-7 | Win-loss 品类复盘制度化 | D9.3 前置；需 ≥2 sent quotes | Business owner | N |

---

## 5. 跨类 SKU 聚焦策略

| 品类 | 30 天主战场 | P0 关联 | P1 关联 | 备注 |
|---|---|---|---|---|
| **Desk Frames** | **Primary** | P0-1~5 全部 | P1-2~4 | HRD + dual-motor 代表 SKU；interval quote 主路径 |
| **Desk Legs** | Secondary（Week 3–4） | P0-3 stability；P0-5 sample | P1-3 finish | `DEFAULT_REVIEWS` delivery P2 已 seed；leg-only load 需单独确认 |
| **Lifting Columns** | Secondary（OEM 向） | P0-2 noise（seed focus） | P1-1 medical/industrial；P1-2 controller | HAT discovery 优先 column/controller，非 complete frame |

---

## 6. 30 天执行表（Week-by-Week）

**总目标：** 在不声称 `STAGING_VALIDATED` 前提下，完成 1 轮「真实 lead → 能力回填 → 报价 → 学习回流」闭环。

### Week 1（Day 1–7）· 证据与数据基线

| Day | 动作 | 产出 | P0/P1 | Owner |
|---|---|---|---|---|
| 1 | 跑 `build_lifting_project_expectations()` + market response（focus: `adjustable_desk_frames`, `desk_legs`, `lifting_columns`） | 缺口清单 CSV（internal） | 全部 | Operator |
| 1–2 | Daily queue 周启动：`/admin/daily-decision-queue` — 确认 HOSUN lifting 项可见 | P0 项入队 | P0 | Operator |
| 2–3 | HOSUN 外部动作：**手动**请求 load + cert + noise + stability 材料（D8.33 流程，非 auto-send） | External execution tracker 更新 | P0-1/2/3, P1-4 | Business owner |
| 3–4 | Catalog 回填：HRD 300kg + top 5 dual-motor + 2 desk legs + 1 column | `attributes_json` 更新；coverage ≥50% on ≥15 SKU | P0-1, P0-4 | Product ops |
| 4–5 | 更新 Market Response reviews：load/noise/cert/stability owner + due date | Reviews 可追踪 | P0-1/2/3, P1-4 | Business owner |
| 5 | 定义 sample SKU（frame ×1, leg ×1）+ internal 审批流程 | Sample prep kit 就绪 | P0-5 | Product ops |
| 6–7 | Real lead discovery（系统外发送）：SWC、HAT、OCI — lifting ≤4 问 | ≥3 touchpoints；missing info 收敛 | P0-5, P1-1 | Sales |

### Week 2（Day 8–14）· 报价包与审查

| Day | 动作 | 产出 | P0/P1 | Owner |
|---|---|---|---|---|
| 8–9 | 构建 **Heavy-duty** + **Standard dual-motor** interval quote 模板（各 1 SKU） | Draft quotes `internal_review` | P0-1 | Sales + ops |
| 10 | Business owner 审查 load/noise/stability wording（D8.26 矩阵） | load review 推进；禁止未验证 300kg 对外 copy | P0-1/2/3 | Business owner |
| 11–12 | 1 份 multi-leg / 3-leg project quote draft | Project quote artifact | P0-4 | Sales |
| 12–13 | Controller compatibility matrix v0 + OEM 孔位询价模板 | Internal matrix doc | P1-2 | Product ops |
| 13–14 | 导入标准 finish 色板 + MOQ；Quote learning 表单预填 dimensions | ≥5 SKU finish_options | P1-3, P0-5 | Product ops |
| 14 | Market intelligence 周三复盘：`/admin/market-intelligence` focus_category | Gap 更新 | 全部 | Operator |

### Week 3（Day 15–21）· 试点报价与客户接触

| Day | 动作 | 产出 | P0/P1 | Owner |
|---|---|---|---|---|
| 15–16 | 向 ≥1 **REAL** lead（SWC 或 OCI 优先）**手动**发送 quote PDF | 1 sent quote（manual sent 记录） | P0-1, P0-5 | Sales |
| 17–18 | Follow-up + quote learning 记录（won/lost/no_response/on_hold） | ≥2 learning records | P0-5 | Sales |
| 19 | Promote ≥1 learning → Market Response review | 新 review 或更新 | P0-2/3, P1-4 | Business owner |
| 20 | Sample 询价 internal rehearsal（D5.14 workflow） | Sample action logged | P0-5 | Operator |
| 20–21 | Daily queue 周审：P0 blocker 状态 | 决策 brief | P0 | Business owner |
| 21 | HAT OEM discovery（column/controller/custom） | ≥1 OEM touchpoint | P1-1, P1-2 | Sales |

### Week 4（Day 22–30）· 复盘与下阶段门禁

| Day | 动作 | 产出 | P0/P1 | Owner |
|---|---|---|---|---|
| 22–24 | Win-loss 按 category 复盘（frames vs legs vs columns） | `d9_market_response_YYYYMMDD.md` 草稿（redacted） | P2-7 | Business owner |
| 25 | `build_lifting_project_expectations()` 复测；priority 重排 | P1→P2 或升级建议 | 全部 | Operator |
| 26–27 | Desk legs path：2 leg SKU quote draft（frame 顺利则提前） | Leg quote optional | P2-1 | Sales |
| 28 | Cert + lead time + warranty wording 汇总审查 | Customer-safe candidate 草稿集 | P1-4 | Business owner |
| 29 | 试点 Go/Continue/Hold 评审 | 书面建议 | 全部 | Business owner |
| 30 | 归档：learning records、reviews、external execution 快照 | 本文档 §8 回填 | 全部 | Operator |

### 固定周节奏

| 节奏 | 动作 | 路径 |
|---|---|---|
| **周一** | Daily decision queue — HOSUN lifting + P0 状态 | `/admin/daily-decision-queue` |
| **周三** | Market intelligence — focus_category + gap | `/admin/market-intelligence` |
| **周五** | Quote detail — learning + promote 审查 | Quote detail → learning tab |

---

## 7. Market Response 录入规范

> 适用于 Market Response Review、Quote Learning promote、Manual market notes。**禁止**将 demo 数据或命名推断写入 `customer-safe candidate`。

### 7.1 必填字段

| 字段 | 说明 | 允许值 / 格式 |
|---|---|---|
| `partner_focus` | 制造伙伴 | `HOSUN`（升降）、`JOOBOO`（教育/项目家具 peer） |
| `focus_category` | 品类 | `adjustable_desk_frames` · `desk_legs` · `lifting_columns` |
| `review_dimension` | 审查维度 | load · stability · noise · delivery · installation · after-sales · packaging · warranty · test cycle · certification · project demand |
| `visibility_class` | 可见性 | `needs validation` · `internal-only` · `customer-safe candidate` · `pilot blocker` |
| `priority` | 优先级 | P0 · P1 · P2（与 daily queue 一致） |
| `status` | 状态 | `needs review` · `watching` · `reviewed` · `blocked` |
| `source_type` | 证据类型 | `market signal` · `feedback` · `quote learning` · `shipment` · `order` · `manual` |
| `source_summary` | 来源摘要 | ≤280 字；**须标注 REAL / ASSUMPTION / DEMO / PENDING** |
| `evidence_summary` | 证据摘要 | 可验证事实；**禁止**编造客户原话或 sign-off |
| `customer_safe_summary` | 客户安全文案 | 仅当 business owner 批准 + 支撑材料存在；否则 `null` |
| `internal_notes` | 内部备注 | raw test notes、complaint、margin、supplier private notes **仅放此处** |
| `next_action` | 下一步 | 可执行、可指派 |
| `owner` | 负责人 | business owner · product ops · operator · engineering liaison |

### 7.2 证据类型标注规则

```text
[REAL]     — 来自 local_data lead batch、已发送 touchpoint、已记录 feedback/quote（可引用公司名）
[ASSUMPTION] — 来自 DEFAULT_REVIEWS、catalog 推断、fit 规则、D5.17 策略
[DEMO]     — 来自 pytest/fixture/seed；禁止进入 evidence_summary
[PENDING]  — 已请求 HOSUN/外部材料，未收到
```

### 7.3 Quote Learning → Market Response 升档条件

引用 `quote_learning.py` → `promote_quote_learning_to_market_response()`：

1. `outcome_status` 为 lost/on_hold 且 dimensions 含 load/noise/certification → 默认 P1。
2. Promote 前 `_assert_safe_text`：不得含 internal cost、margin、supplier private、raw token。
3. 升档后 visibility 默认 `needs validation`（lost）或 `internal-only`（若 `internal_only=true`）。
4. **单条 learning 不作结论** — 与 `single_feedback_is_not_conclusion: true` 一致；需 ≥2 条同维度或 + HOSUN 材料方可 → `reviewed`。

### 7.4 Customer-Safe 门槛（D8.26）

load、noise、stability、test cycle、certification、warranty **同时满足**：

1. Business owner 确认 exact customer-safe wording。
2. Supporting product material 存在且 approved for external use。

否则：`visibility_class = needs validation`，Portal/quote PDF **不得**使用推断值。

### 7.5 禁止事项

- 写入 `STAGING_VALIDATED` 或 real business owner sign-off（除非真实证据归档）。
- 将 `heavy_duty_rule` 推断 300kg 作为已批准 load claim。
- 对外 medical/industrial compliance 声明。
- 自动 email / 自动改 quote status（系统 safety 边界）。

---

## 8. 首波试点建议（First Pilot Recommendations）

### 8.1 立即启动（Day 1–3）

1. **P0-1 + P0-4 合并路径：** 选 1 款 HRD/300kg **或** 3-leg project 代表 SKU（二选一，避免分散）→ 回填 `load_capacity_kg` + `width_range_mm` → internal interval quote。
2. **P0-5 样品 + REAL lead：** SWC 或 OCI（dealer/lift，`REAL`）优先 — 已有 product focus 与 missing info 记录；discovery ≤4 问，不 auto-send。
3. **P0-2/3 材料请求：** 通过 external execution console **手动**向 HOSUN 索取 load/noise/stability **summary**（非 raw notes）。

### 8.2 30 天最小成功定义（MVP）

| # | 条件 | 验证方式 |
|---|---|---|
| 1 | ≥1 **manual sent** lifting quote PDF | Quote send tracking + learning record |
| 2 | ≥3 quote learning records | Quote learning API / admin |
| 3 | ≥1 Market Response review → `reviewed`（load 或 cert 优先） | Market response console |
| 4 | ≥15 SKU capability coverage ≥50% | `build_lifting_project_expectations()` |
| 5 | **零**未批准 300kg / cert / medical 对外 claim | D8.26 audit + quote PDF review |

### 8.3 不建议现在做

- 对外 medical/industrial 合规声明。
- 基于命名推断的 300kg 全球推广 copy。
- 自动 noise/load marketing copy。
- 进入 D9.3 正式 operating loop（需 D8 Go/No-Go + ≥2 sent quotes + P0 解除）。

### 8.4 30 天后分支

| 结果 | 建议 |
|---|---|
| MVP 5/5 达成 | Phase B：desk legs/columns 扩展 + Portal heavy-duty staging rehearsal |
| MVP 3–4/5 | Continue 30 天：补 P0 load/cert 材料；Hold Portal claims |
| MVP ≤2/5 | Hold pilot claims；回到 catalog 回填 + HOSUN 材料追踪 |

---

## 9. P0 / P1 / P2 总览（Orchestrator 摘要）

| 优先级 | 项数 | 主题 | 30 天核心交付 |
|---|---|---|---|
| **P0** | 5 | 300kg · noise · stability · multi-leg/conference · samples+feedback | 1 sent quote · reviews 推进 · ≥15 SKU 回填 · sample SKU 定义 |
| **P1** | 4 | medical/industrial · mounting+controller · finish/assembly · cert/warranty/lead time | cert index · controller matrix · finish 色板 · OEM discovery |
| **P2** | 7 | legs/columns 扩展 · UI · staging · 深度 cert · multi-leg 控制 · win-loss 制度 | 视 P0 进度并行或顺延 |

---

## 10. 变更记录

| Date | Agent | Change |
|---|---|---|
| 2026-07-26 | D | 初版：P0/P1/P2 全字段矩阵 + 30 天执行表 + Market Response 规范 + 首波建议 |

---

**Related:** `docs/records/lifting_pilot_backlog_20260726.md`（Agent E backlog，供交叉引用）
