<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

type ExternalActionStatus = 'draft' | 'ready to send' | 'sent manually' | 'response received' | 'blocked' | 'complete'

interface ExternalAction {
  id: string
  actionType: string
  owner: string
  dueDate: string
  dependency: string
  nextStep: string
  status: ExternalActionStatus
  notes: string
}

const STORAGE_KEY = 'partneros.externalExecutionTracker.v1'

const statusOptions: ExternalActionStatus[] = [
  'draft',
  'ready to send',
  'sent manually',
  'response received',
  'blocked',
  'complete',
]

const statusLabels: Record<ExternalActionStatus, string> = {
  draft: '草稿',
  'ready to send': '待人工发送',
  'sent manually': '已人工发送',
  'response received': '已收到真实回复',
  blocked: '阻塞',
  complete: '完成',
}

const statusType: Record<ExternalActionStatus, 'info' | 'primary' | 'warning' | 'success' | 'danger'> = {
  draft: 'info',
  'ready to send': 'primary',
  'sent manually': 'warning',
  'response received': 'success',
  blocked: 'danger',
  complete: 'success',
}

const templateActions: ExternalAction[] = [
  {
    id: 'EXT-001',
    actionType: 'partner rehearsal request',
    owner: '业务负责人',
    dueDate: '待排期',
    dependency: 'partner rehearsal message + feedback form',
    nextStep: '手动邀请 HOSUN/JOOBOO/未来 partner，演示后再录入真实反馈。',
    status: 'ready to send',
    notes: '没有真实回复前不得标记 response received。',
  },
  {
    id: 'EXT-002',
    actionType: 'business UAT / data sign-off request',
    owner: '业务负责人',
    dueDate: '待排期',
    dependency: 'UAT data selection + customer-safe wording checklist',
    nextStep: '确认 customer-visible 字段、禁止字段、样本数据和 pilot 产品范围。',
    status: 'draft',
    notes: '没有 owner/date/scope 的真实签字前不得写 approved。',
  },
  {
    id: 'EXT-003',
    actionType: 'security review request',
    owner: '安全审核人',
    dueDate: '待排期',
    dependency: 'forbidden field matrix + secret handling drill',
    nextStep: '审核 token、CORS、日志、截图、回滚和 customer-safe 白名单。',
    status: 'draft',
    notes: '不处理真实 token；raw token 不能进入文档、日志、截图或聊天。',
  },
  {
    id: 'EXT-004',
    actionType: 'staging credentials request',
    owner: '部署/Portal 负责人',
    dueDate: '待排期',
    dependency: 'backend HTTPS origin + Portal origin + allowed origins + PUBLIC_BASE_URL',
    nextStep: '通过安全渠道接收配置，只记录 PROVIDED_VIA_SECURE_CHANNEL 等脱敏状态。',
    status: 'draft',
    notes: '当前外部 staging 仍是 WAITING_FOR_REAL_STAGING_EVIDENCE。',
  },
  {
    id: 'EXT-005',
    actionType: 'staging smoke execution',
    owner: '联调负责人',
    dueDate: '真实 credentials 到位后',
    dependency: 'security signoff + business signoff + UAT seed approval + rollback owner',
    nextStep: '运行真实 staging smoke；全部通过前不能写 STAGING_VALIDATED，不能进入 D9。',
    status: 'blocked',
    notes: '被真实 credentials/evidence/sign-off 阻塞。',
  },
]

const actions = ref<ExternalAction[]>(structuredClone(templateActions))

const stagingReadiness = [
  ['backend HTTPS origin', 'pending external input', '需要真实后端 HTTPS 地址，不能用本地 URL 替代。'],
  ['service.intelli-opus.com real origin', 'pending external input', '需要 Portal 侧真实 origin。'],
  ['PORTAL_CUSTOMER_API_TOKEN', 'pending secure channel', '只允许记录 PROVIDED_VIA_SECURE_CHANNEL，不记录 token 原文。'],
  ['PORTAL_CUSTOMER_ALLOWED_ORIGINS', 'pending external input', '必须明确允许 origin，不能使用 wildcard。'],
  ['PUBLIC_BASE_URL', 'pending external input', '需要与真实 staging 域名一致。'],
  ['security signoff', 'pending', '需要 reviewer/date/scope。'],
  ['business signoff', 'pending', '需要 owner/date/scope。'],
  ['real staging smoke test', 'pending', '本地 dry-run 和脚本通过不等于真实 staging validated。'],
  ['D9 entry gate', 'blocked', '任一 P0 条件缺失都不得进入 D9。'],
]

const hosunFieldRows = [
  ['load', 'customer-safe candidate', '需要资料支持；未经业务确认不得给客户看。'],
  ['stability', 'customer-safe candidate', '可转为 stability summary，原始测试记录 internal-only。'],
  ['noise', 'needs validation', 'noise claim 需要确认测试条件和话术。'],
  ['delivery', 'customer-safe candidate', '只能展示预计交期或客户可接受表述。'],
  ['installation', 'customer-safe candidate', '可展示安装摘要，内部问题归因不外露。'],
  ['after-sales', 'customer-safe candidate', '可展示售后支持摘要。'],
  ['packaging', 'customer-safe candidate', '可展示包装摘要，供应商备注 internal-only。'],
  ['warranty', 'needs validation', 'warranty summary 需要业务确认。'],
  ['test cycle', 'needs validation', '测试周期需资料支持后才能 customer-visible。'],
  ['certification', 'needs validation', '认证字段必须有材料支持。'],
  ['project demand', 'customer-safe candidate', '项目制需求可高层展示，内部评分不外露。'],
]

const partnerCoverage = [
  {
    partner: 'HOSUN',
    focus: 'lifting systems / desk frames / desk legs / lifting columns / heavy-duty supply',
    rule: '技术声称必须区分 customer-safe candidate、needs validation、internal-only、pilot blocker。',
  },
  {
    partner: 'JOOBOO',
    focus: 'education furniture / school desks/chairs / project furniture',
    rule: '关注 school procurement timing、delivery consistency、installation、resource needs、feedback after use、project acceptance criteria。',
  },
  {
    partner: 'future partner',
    focus: 'onboarding data / product family / quote logic / delivery requirement / resource taxonomy',
    rule: '沿用同一闭环，但保留各自 customer-visible fields 和 Market Response metrics。',
  },
]

const hasUnsafeStatus = computed(() =>
  actions.value.some((action) => action.status === 'response received' || action.status === 'complete'),
)

onMounted(() => {
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return
  try {
    const parsed = JSON.parse(raw) as ExternalAction[]
    const ids = new Set(templateActions.map((item) => item.id))
    if (Array.isArray(parsed) && parsed.every((item) => ids.has(item.id))) {
      actions.value = parsed
    }
  } catch {
    window.localStorage.removeItem(STORAGE_KEY)
  }
})

function saveTracker() {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(actions.value))
}

function resetTracker() {
  actions.value = structuredClone(templateActions)
  saveTracker()
}

function statusLabel(status: ExternalActionStatus) {
  return statusLabels[status]
}

function statusTagType(status: ExternalActionStatus) {
  return statusType[status]
}
</script>

<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">外部执行 / Staging Readiness</h2>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          用于内部 Beta 的人工执行跟踪：记录 partner rehearsal、business UAT、security review、staging credentials 和真实 staging smoke 的状态。系统只记录人工状态，不自动发送邮件、短信、LinkedIn 或客户通知。
        </p>
      </div>
      <div class="flex gap-2">
        <el-button @click="resetTracker">恢复模板</el-button>
        <el-button type="primary" @click="saveTracker">保存到本机</el-button>
      </div>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="当前仍是 READY_FOR_STAGING_HANDOFF；外部 staging 仍是 WAITING_FOR_REAL_STAGING_EVIDENCE。没有真实回复不能标记 response received；没有真实签字不能 approved；不能记录 raw token；不能进入 D9。"
    />
    <el-alert
      v-if="hasUnsafeStatus"
      type="info"
      :closable="false"
      title="请确认：response received / complete 只能在用户贴出真实外部回复、真实验证或真实签字后使用。"
    />

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 class="font-semibold text-slate-800">手动外部执行 Tracker</h3>
        <el-tag type="info" effect="plain">API cost $0 / no external send</el-tag>
      </div>
      <el-table :data="actions" border size="small">
        <el-table-column prop="id" label="ID" width="86" />
        <el-table-column prop="actionType" label="Action type" min-width="190" />
        <el-table-column prop="owner" label="Owner" width="130" />
        <el-table-column prop="dueDate" label="Due date" width="150">
          <template #default="{ row }">
            <el-input v-model="row.dueDate" size="small" @change="saveTracker" />
          </template>
        </el-table-column>
        <el-table-column prop="dependency" label="Dependency" min-width="220" />
        <el-table-column prop="nextStep" label="Next step" min-width="260" />
        <el-table-column label="Status" width="190">
          <template #default="{ row }">
            <el-select v-model="row.status" size="small" @change="saveTracker">
              <el-option v-for="status in statusOptions" :key="status" :label="statusLabel(status)" :value="status" />
            </el-select>
            <el-tag class="mt-1" :type="statusTagType(row.status)" effect="plain">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Notes" min-width="230">
          <template #default="{ row }">
            <el-input v-model="row.notes" type="textarea" :rows="3" @change="saveTracker" />
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 class="font-semibold text-slate-800">Staging Readiness Gate</h3>
        <el-tag type="danger" effect="plain">D9 gate blocked</el-tag>
      </div>
      <div class="grid gap-3 md:grid-cols-3">
        <div v-for="row in stagingReadiness" :key="row[0]" class="rounded border border-slate-100 bg-slate-50 p-3">
          <div class="text-sm font-semibold text-slate-800">{{ row[0] }}</div>
          <el-tag class="my-2" type="warning" effect="plain">{{ row[1] }}</el-tag>
          <p class="text-xs text-slate-600">{{ row[2] }}</p>
        </div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 class="font-semibold text-slate-800">HOSUN 升降系统字段边界</h3>
        <el-tag effect="plain">lifting systems / desk frames / desk legs / lifting columns / heavy-duty supply</el-tag>
      </div>
      <el-table :data="hosunFieldRows" border size="small">
        <el-table-column label="Field" width="150">
          <template #default="{ row }">{{ row[0] }}</template>
        </el-table-column>
        <el-table-column label="Review class" width="190">
          <template #default="{ row }">
            <el-tag effect="plain">{{ row[1] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Rule">
          <template #default="{ row }">{{ row[2] }}</template>
        </el-table-column>
      </el-table>
      <p class="mt-3 text-xs text-slate-500">
        raw test notes、complaint details、delivery risk analysis、warranty cost exposure、supplier private notes、internal Market Response scoring/ranking 必须 internal-only。
      </p>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <h3 class="mb-3 font-semibold text-slate-800">多 Partner 平级执行规则</h3>
      <div class="grid gap-3 md:grid-cols-3">
        <div v-for="item in partnerCoverage" :key="item.partner" class="rounded border border-slate-100 bg-slate-50 p-3">
          <div class="text-sm font-semibold text-slate-900">{{ item.partner }}</div>
          <p class="mt-2 text-sm text-slate-600">{{ item.focus }}</p>
          <p class="mt-2 text-xs text-slate-500">{{ item.rule }}</p>
        </div>
      </div>
    </section>
  </div>
</template>
