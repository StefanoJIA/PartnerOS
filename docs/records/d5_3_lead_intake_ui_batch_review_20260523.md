# D5.3 Lead Intake UI & Batch Review

## Goal

把 CLI lead import preview 推进为前端可用的 lead intake 页面。

## Workflow

1. 准备 CSV（`docs/templates/lead_import_template.csv` 或 Download CSV Template）。
2. 打开 `/lead-intake`。
3. 粘贴或上传 CSV。
4. 点击 **Preview**。
5. 检查 missing fields、duplicate status、likely segments、recommended next action。
6. 无 ERROR 行后点击 **Confirm Import**（WARN 行需确认）。
7. 点击 **Go to Manual Outreach Queue** → `/lead-intelligence`。
8. 继续 **Generate Draft** / **Mark as Sent**（人工外发，系统不自动发送）。

## API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/a-domain/lead-intake/template` | 下载 CSV 模板 |
| POST | `/api/a-domain/lead-intake/preview` | 只读预检 |
| POST | `/api/a-domain/lead-intake/apply` | 确认导入（`confirm: true`） |

Service 层：`preview_lead_csv_text` / `apply_lead_csv_text`（`lead_import_service.py`），CLI 与 API 共用。

## Safety

- no automatic sending
- no LinkedIn automation
- no Outlook integration
- no private CSV committed to git
- CSV 仅在内存 / 请求体中处理，不写入 repo

## Acceptance Criteria

- [x] preview works
- [x] duplicate warning works
- [x] apply requires confirm=true
- [x] apply reuses idempotent import logic
- [x] imported leads appear in `/lead-intelligence`
- [x] pytest / vitest pass
