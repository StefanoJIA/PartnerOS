# D5.4 Lead Completeness & Contact Research Queue

## Goal

帮助用户在外联前识别哪些 lead 资料不完整，优先补全联系人、网站、next action 和 enrichment。

## Workflow

1. 打开 `/lead-intelligence`。
2. 查看 **Lead Completeness** summary cards。
3. 筛选 **Needs Contact Research** 或 **Missing Email / LinkedIn**。
4. 点击行加载 workflow，补联系人信息（公司/联系人详情页）。
5. 使用 **Contact research preset** 记录 touchpoint。
6. 筛选 **Ready for Outreach** 或 **Complete**。
7. **Generate Draft** → 人工发送 → **Mark as Sent**。

## API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/a-domain/lead-completeness` | 只读完整度 board（所有 active leads） |

前端在 `/lead-intelligence` 使用相同规则 derived 计算（`constants/leadCompleteness.ts`）。

## Completeness 规则

| 区块 | 分值 |
|------|------|
| Company basics | 30（name / type-industry-notes / website） |
| Contact basics | 30（name / title / email-or-LinkedIn / phone） |
| Lead intelligence | 20（segment / score / next action hint） |
| Outreach readiness | 20（next_action / enrichment / touchpoint / draft-ready） |

| 分数 | 状态 |
|------|------|
| 80–100 | Complete |
| 60–79 | Ready for Outreach |
| 40–59 | Needs Contact Research |
| 0–39 | Incomplete |

## Safety

- no automatic LinkedIn search
- no scraping
- no automatic sending
- human-reviewed workflow only

## Acceptance Criteria

- [x] completeness score 可见
- [x] missing fields 可见
- [x] research queue 可筛选
- [x] ready leads 可继续进入 draft
- [x] tests pass
