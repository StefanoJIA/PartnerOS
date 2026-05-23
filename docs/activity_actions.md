# Activity log actions (canonical)

`activity_logs.action` strings emitted by the API. Names are stable for filtering and audits.

| 列 | 含义 |
|----|------|
| **触发场景** | 典型触发 API / 业务动作（供验收与审计对照；非穷尽代码路径）。 |

## CRM

| Action | Object type | Notes | 触发场景 |
|--------|-------------|--------|----------|
| `company_created` | company | | `POST /companies` |
| `company_updated` | company | | `PUT /companies/{id}` |
| `contact_created` | contact | | `POST /contacts` |
| `contact_added_from_company` | company | `diff.contact_id` | 自公司页创建联系人并挂载 |
| `contact_updated` | contact | | `PUT /contacts/{id}` |
| `lead_created` | lead | | `POST /leads` |
| `lead_created_from_company` | company | | 创建线索且关联公司 |
| `lead_created_from_contact` | contact | | 创建线索且关联联系人 |
| `lead_updated` | lead | | `PUT /leads/{id}` |
| `lead_stage_changed` | lead | | `POST /leads/{id}/stage` |
| `rfq_created_from_lead` | lead | | 自线索创建 RFQ |
| `sample_created_from_lead` | lead | | 自线索创建样品 |

## Tasks & interactions

| Action | Object type | Notes | 触发场景 |
|--------|-------------|--------|----------|
| `task_created` | task, or related object | Also logged on related CRM/RFQ/etc. | `POST /tasks` 等 |
| `task_completed` | task | | 完成任务接口 |
| `interaction_created` | related object | | `POST /interactions` |
| `interaction_spawned_task` | related object | | 互动拆分任务 |

## Partners & products

| Action | Object type | Notes | 触发场景 |
|--------|-------------|--------|----------|
| `partner_created` | manufacturing_partner | | `POST /manufacturing-partners` |
| `partner_updated` | manufacturing_partner | | `PUT /manufacturing-partners/{id}` |
| `product_created` | product | | `POST /products` |
| `product_updated` | product | | `PUT /products/{id}` |
| `partner_linked` | product | | `POST /products/{id}/partners` |
| `partner_link_updated` | product | | `PUT .../partners` 关联更新 |
| `partner_unlinked` | product | | 解除产品与工厂关联 |
| `product_linked` | manufacturing_partner | Mirror event | 自工厂侧链接产品 |
| `product_link_updated` | manufacturing_partner | | 工厂侧关联更新 |
| `product_unlinked` | manufacturing_partner | | 工厂侧解除关联 |

## RFQ & quotations

| Action | Object type | Notes | 触发场景 |
|--------|-------------|--------|----------|
| `rfq_created` | rfq | | `POST /rfqs` |
| `rfq_updated` | rfq | | `PUT /rfqs/{id}` |
| `rfq_status_changed` | rfq | | RFQ 状态管线更新 |
| `rfq_item_added` | rfq | | 添加行项目 |
| `rfq_item_updated` | rfq | | 编辑行项目 |
| `rfq_item_removed` | rfq | | 删除行项目 |
| `rfq_partner_candidate_added` | rfq | | 添加候选工厂 |
| `rfq_partner_candidate_updated` | rfq | | 更新候选 |
| `rfq_partner_candidate_removed` | rfq | | 移除候选 |
| `rfq_partner_quote_requested` | rfq | | 标记已询价 |
| `rfq_partner_quote_received` | rfq | | 标记已回价 |
| `quotation_added` | rfq | | 添加伙伴报价 |
| `quotation_updated` | rfq | | 更新报价 |
| `quotation_deleted` | rfq | | 删除报价 |
| `rfq_converted_to_sample` | rfq | | RFQ → 样品 |
| `rfq_converted_to_order` | rfq | | RFQ → 订单 |

## Sample

| Action | Object type | Notes | 触发场景 |
|--------|-------------|--------|----------|
| `sample_created` | sample | | `POST /samples` |
| `sample_created_from_rfq` | sample | | 自 RFQ 转样品 |
| `sample_status_changed` | sample | | `POST /samples/{id}/status` |
| `sample_shipping_updated` | sample | | 样品物流字段更新 |
| `sample_feedback_recorded` | sample | | 客户反馈 |
| `sample_converted_to_order` | sample | | 样品 → 订单 |

## Order

| Action | Object type | Notes | 触发场景 |
|--------|-------------|--------|----------|
| `order_created` | order | | `POST /orders` |
| `order_created_from_rfq` | order | | 自 RFQ 建单 |
| `order_created_from_sample` | order | | 自样品建单 |
| `order_production_status_changed` | order | | `POST .../production-status` |
| `order_shipping_status_changed` | order | | `POST .../shipping-status` |
| `order_milestones_generated` | order | | `POST .../generate-milestones` |
| `order_milestone_updated` | order | | `PUT .../milestones/{id}` |
| `order_milestone_completed` | order | | `POST .../milestones/{id}/complete` |
| `order_milestone_delayed` | order | | `POST .../milestones/{id}/delayed` |
| `shipping_record_added` | order | | 新建海运记录 |
| `shipping_record_updated` | order | | `PUT .../shipping-records/{id}` |
| `shipping_record_deleted` | order | | 删除海运记录（若实现） |
| `shipping_customs_cleared` | order | | 清关完成快捷动作 |
| `shipping_warehouse_inbound` | order | | 入仓 |
| `shipping_final_delivered` | order | | 最终交付 |

## Files, tags, notes, AI（Object）

| Action | Object type | Notes | 触发场景 |
|--------|-------------|--------|----------|
| `file_uploaded` | file | Binary stored via `/files/upload` | 文件上传 |
| `file_deleted` | file | | 删除文件 |
| `file_attached` | target object | After attach to entity | 附件挂载到业务对象 |
| `tag_attached` | target object | | 打标签 |
| `tag_detached` | target object | | 移除标签 |
| `note_created` | target object | | 备注创建 |
| `note_updated` | target object | | 备注更新 |
| `note_deleted` | target object | | 备注删除 |
| `ai_output_generated` | target object or `ai_output` | | AI 生成结果落库 |

## Soft delete (legacy name)

| Action | Object type | Notes | 触发场景 |
|--------|-------------|--------|----------|
| `soft_deleted` | various | Deactivate / soft-delete on several resources | 各资源软删/停用 |

These names are used in API handlers under `app/api/routes/` and `app/services/`.
