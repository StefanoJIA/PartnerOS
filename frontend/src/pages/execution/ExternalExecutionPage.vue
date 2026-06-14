<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { formatApiError } from '@/api/errors'
import {
  createExternalExecutionAction,
  fetchExternalExecutionConsole,
  updateExternalExecutionAction,
  type ExternalActionStatus,
  type ExternalExecutionAction,
  type ExternalExecutionActionPayload,
  type ExternalExecutionConsole,
} from '@/api/externalExecution'
import OperationalTracePanel from '@/components/dashboard/OperationalTracePanel.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const consoleData = ref<ExternalExecutionConsole | null>(null)
const intakeVisible = ref(false)
const intakeAction = ref<ExternalExecutionAction | null>(null)

const newAction = reactive({
  action_type: 'partner rehearsal request',
  target_partner_system: '',
  partner_focus: '',
  product_focus_text: '',
  owner: '',
  due_date: '',
  dependency: '',
  next_step: '',
  status: 'draft' as ExternalActionStatus,
  notes: '',
})
const filters = reactive({
  status: '',
  action_type: '',
  owner: '',
  keyword: '',
})
const externalFilterKeys = ['status', 'action_type', 'owner', 'keyword'] as const
type ExternalFilterKey = (typeof externalFilterKeys)[number]
const intakeForm = reactive({
  status: 'draft' as ExternalActionStatus,
  response_summary: '',
  risk_notes: '',
  blocker_notes: '',
  redacted_credential_status: '',
  notes: '',
})

const statusType: Record<ExternalActionStatus, 'info' | 'primary' | 'warning' | 'success' | 'danger'> = {
  draft: 'info',
  'ready to send': 'primary',
  'sent manually': 'warning',
  'response received': 'success',
  blocked: 'danger',
  complete: 'success',
}
const redactedCredentialOptions = [
  { value: '', label: '未收到 / 不适用' },
  { value: 'pending', label: 'pending' },
  { value: 'PROVIDED_VIA_SECURE_CHANNEL', label: 'PROVIDED_VIA_SECURE_CHANNEL' },
  { value: 'configured without raw value', label: 'configured without raw value' },
  { value: 'verified without raw value', label: 'verified without raw value' },
  { value: 'rejected or incomplete', label: 'rejected or incomplete' },
]
const tokenLikeMarkers = ['bearer ', 'authorization:', 'api_key', 'api-key', 'token=', 'sk-', 'ghp_', 'xoxb-', 'actual-secret']

const actions = computed(() => consoleData.value?.actions || [])
const actionTypeOptions = computed(() => Array.from(new Set(actions.value.map((row) => row.action_type))).sort())
const filteredActions = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  const owner = filters.owner.trim().toLowerCase()
  const statusOrder: Record<string, number> = {
    blocked: 0,
    'ready to send': 1,
    draft: 2,
    'sent manually': 3,
    'response received': 4,
    complete: 5,
  }
  return actions.value
    .filter((row) => {
      if (filters.status && row.status !== filters.status) return false
      if (filters.action_type && row.action_type !== filters.action_type) return false
      if (owner && !(row.owner || '').toLowerCase().includes(owner)) return false
      if (!keyword) return true
      return [
        row.action_type,
        row.target_partner_system,
        row.partner_focus || '',
        row.product_focus.join(' '),
        row.dependency || '',
        row.next_step || '',
        row.response_summary || '',
        row.risk_notes || '',
        row.blocker_notes || '',
        row.notes || '',
      ]
        .join(' ')
        .toLowerCase()
        .includes(keyword)
    })
    .sort((left, right) => {
      const statusDiff = (statusOrder[left.status] ?? 99) - (statusOrder[right.status] ?? 99)
      if (statusDiff) return statusDiff
      const leftDue = left.due_date || '9999-12-31'
      const rightDue = right.due_date || '9999-12-31'
      return leftDue.localeCompare(rightDue) || left.target_partner_system.localeCompare(right.target_partner_system)
    })
})
const statusOptions = computed(() => consoleData.value?.status_options || [])
const stagingReadiness = computed(() => consoleData.value?.staging_readiness || [])
const readinessGaps = computed(() => consoleData.value?.readiness_gap_intelligence || [])
const hosunFieldRows = computed(() => consoleData.value?.lifting_systems_field_review || [])
const partnerCoverage = computed(() => consoleData.value?.partner_coverage || [])
const readinessGapSummary = computed(() => {
  const gaps = readinessGaps.value
  return {
    p0: gaps.filter((gap) => gap.severity === 'P0').length,
    d9: gaps.filter((gap) => gap.affects_d9).length,
    pilot: gaps.filter((gap) => gap.affects_pilot).length,
    blocked: gaps.filter((gap) => gap.work_state === 'blocked').length,
  }
})
const activeExternalFilterLabel = computed(() => {
  const labels: string[] = []
  if (filters.status) labels.push(`状态=${filters.status}`)
  if (filters.action_type) labels.push(`动作=${filters.action_type}`)
  if (filters.owner) labels.push(`负责人=${filters.owner}`)
  if (filters.keyword) labels.push(`关键词=${filters.keyword}`)
  return labels.length ? labels.join(' / ') : '全部外部动作'
})

const hasSensitiveBoundary = computed(() =>
  Boolean(consoleData.value?.status === 'READY_FOR_STAGING_HANDOFF' && consoleData.value?.external_staging_state),
)

function statusTagType(status: ExternalActionStatus) {
  return statusType[status]
}

function splitProductFocus(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function applyConsole(next: ExternalExecutionConsole) {
  consoleData.value = next
}

function routeQueryString(key: ExternalFilterKey) {
  const value = route.query[key]
  return typeof value === 'string' ? value : ''
}

function syncFiltersFromRoute() {
  filters.status = routeQueryString('status') as ExternalActionStatus | ''
  filters.action_type = routeQueryString('action_type')
  filters.owner = routeQueryString('owner')
  filters.keyword = routeQueryString('keyword')
}

function externalFilterQuerySignature() {
  return externalFilterKeys.map((key) => `${key}:${routeQueryString(key)}`).join('|')
}

async function applyExternalFilters() {
  const before = externalFilterQuerySignature()
  const query = { ...route.query }
  for (const key of externalFilterKeys) {
    const value = String(filters[key]).trim()
    if (value) {
      query[key] = value
    } else {
      delete query[key]
    }
  }
  await router.replace({ path: route.path, query })
  if (before === externalFilterQuerySignature()) {
    syncFiltersFromRoute()
  }
}

function applyStatusFilter(status: ExternalActionStatus | '') {
  filters.status = status
  void applyExternalFilters()
}

function onStatusFilterChange(value: string) {
  applyStatusFilter((value || '') as ExternalActionStatus | '')
}

function onExternalFilterChange() {
  void applyExternalFilters()
}

function resetFilters() {
  filters.status = ''
  filters.action_type = ''
  filters.owner = ''
  filters.keyword = ''
  void applyExternalFilters()
}

function toNullable(value: string) {
  const trimmed = value.trim()
  return trimmed ? trimmed : null
}

function hasTokenLikeText(...values: string[]) {
  const text = values.join('\n').toLowerCase()
  return tokenLikeMarkers.some((marker) => text.includes(marker))
}

function openIntake(row: ExternalExecutionAction) {
  intakeAction.value = row
  intakeForm.status = row.status
  intakeForm.response_summary = row.response_summary || ''
  intakeForm.risk_notes = row.risk_notes || ''
  intakeForm.blocker_notes = row.blocker_notes || ''
  intakeForm.redacted_credential_status = row.redacted_credential_status || ''
  intakeForm.notes = row.notes || ''
  intakeVisible.value = true
}

function validateIntake() {
  if (intakeForm.status === 'response received' && !intakeForm.response_summary.trim()) {
    return '标记 response received 前必须录入真实回复摘要。'
  }
  if (hasTokenLikeText(intakeForm.response_summary, intakeForm.risk_notes, intakeForm.blocker_notes, intakeForm.redacted_credential_status, intakeForm.notes)) {
    return '录入内容疑似包含 raw token 或 credential，请改为 PROVIDED_VIA_SECURE_CHANNEL 等脱敏状态。'
  }
  return ''
}

async function saveIntake() {
  if (!intakeAction.value) return
  const validationError = validateIntake()
  if (validationError) {
    error.value = validationError
    ElMessage.error(validationError)
    return
  }
  saving.value = true
  error.value = ''
  try {
    applyConsole(
      await updateExternalExecutionAction(intakeAction.value.id, {
        status: intakeForm.status,
        response_summary: toNullable(intakeForm.response_summary),
        risk_notes: toNullable(intakeForm.risk_notes),
        blocker_notes: toNullable(intakeForm.blocker_notes),
        redacted_credential_status: toNullable(intakeForm.redacted_credential_status),
        notes: toNullable(intakeForm.notes),
      }),
    )
    ElMessage.success('真实回复录入已保存')
    intakeVisible.value = false
    intakeAction.value = null
  } catch (e) {
    error.value = formatApiError(e, '真实回复录入保存失败。')
    await load()
  } finally {
    saving.value = false
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    applyConsole(await fetchExternalExecutionConsole())
  } catch (e) {
    error.value = formatApiError(e, '外部执行协作台加载失败。')
  } finally {
    loading.value = false
  }
}

async function createAction() {
  if (!newAction.target_partner_system.trim()) {
    error.value = '请先填写 target partner/system。'
    return
  }
  saving.value = true
  error.value = ''
  try {
    const payload = {
      action_type: newAction.action_type,
      target_partner_system: newAction.target_partner_system,
      partner_focus: newAction.partner_focus || null,
      product_focus: splitProductFocus(newAction.product_focus_text),
      owner: newAction.owner || null,
      due_date: newAction.due_date || null,
      dependency: newAction.dependency || null,
      next_step: newAction.next_step || null,
      status: newAction.status,
      notes: newAction.notes || null,
    }
    applyConsole(await createExternalExecutionAction(payload))
    newAction.target_partner_system = ''
    newAction.partner_focus = ''
    newAction.product_focus_text = ''
    newAction.owner = ''
    newAction.due_date = ''
    newAction.dependency = ''
    newAction.next_step = ''
    newAction.status = 'draft'
    newAction.notes = ''
    ElMessage.success('已保存外部执行动作')
  } catch (e) {
    error.value = formatApiError(e, '外部执行动作保存失败。')
  } finally {
    saving.value = false
  }
}

async function saveAction(row: ExternalExecutionAction, payload: ExternalExecutionActionPayload) {
  saving.value = true
  error.value = ''
  try {
    applyConsole(await updateExternalExecutionAction(row.id, payload))
    ElMessage.success('已更新')
  } catch (e) {
    error.value = formatApiError(e, '外部执行动作更新失败。')
    await load()
  } finally {
    saving.value = false
  }
}

function editablePayload(row: ExternalExecutionAction): ExternalExecutionActionPayload {
  return {
    owner: row.owner,
    due_date: row.due_date,
    dependency: row.dependency,
    next_step: row.next_step,
    status: row.status,
    response_summary: row.response_summary,
    risk_notes: row.risk_notes,
    blocker_notes: row.blocker_notes,
    redacted_credential_status: row.redacted_credential_status,
    notes: row.notes,
  }
}

onMounted(() => {
  syncFiltersFromRoute()
  load()
})
watch(
  () => [route.query.status, route.query.action_type, route.query.owner, route.query.keyword],
  () => {
    syncFiltersFromRoute()
  },
)
</script>

<template>
  <div class="space-y-5" v-loading="loading">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">外部执行 / Staging Readiness</h2>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          内部协作台：记录 partner rehearsal、business UAT、security review、staging credentials、pilot readiness 和真实 staging smoke 的人工跟进状态。系统只保存人工状态，不自动发送邮件、短信、LinkedIn 或客户通知。
        </p>
      </div>
      <div class="flex gap-2">
        <el-button @click="load">刷新</el-button>
        <el-button type="primary" :loading="saving" @click="createAction">新增动作</el-button>
      </div>
    </div>

    <el-alert
      v-if="hasSensitiveBoundary"
      type="warning"
      :closable="false"
      show-icon
      :title="`当前仍是 ${consoleData?.status}；外部 staging 仍是 ${consoleData?.external_staging_state}。没有真实回复不能标记 response received；没有真实签字不能 approved；不能记录 raw token；不能进入 D9。`"
    />
    <el-alert v-if="error" type="error" :closable="false" :title="error" />

    <OperationalTracePanel
      title="Daily Queue 处理回流"
      description="显示从 Daily Queue 回流到 External Execution 的内部处理记录：谁接手、是否等待外部输入、阻塞原因和最近内部决策。"
      category="external execution"
    />

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 class="font-semibold text-slate-800">新增手动外部动作</h3>
        <el-tag type="info" effect="plain">API cost $0 / no external send</el-tag>
      </div>
      <div class="grid gap-3 lg:grid-cols-3">
        <el-input v-model="newAction.action_type" placeholder="Action type" />
        <el-input v-model="newAction.target_partner_system" placeholder="Target partner/system" />
        <el-input v-model="newAction.partner_focus" placeholder="Partner focus，例如 HOSUN / JOOBOO" />
        <el-input v-model="newAction.product_focus_text" placeholder="Product focus，逗号分隔" />
        <el-input v-model="newAction.owner" placeholder="Owner" />
        <el-input v-model="newAction.due_date" placeholder="Due date: YYYY-MM-DD 或留空" />
      </div>
      <div class="mt-3 grid gap-3 lg:grid-cols-3">
        <el-input v-model="newAction.dependency" type="textarea" :rows="2" placeholder="Dependency" />
        <el-input v-model="newAction.next_step" type="textarea" :rows="2" placeholder="Next step" />
        <el-input v-model="newAction.notes" type="textarea" :rows="2" placeholder="Notes，不要粘贴 raw token" />
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="font-semibold text-slate-800">手动外部执行 Tracker</h3>
          <p class="mt-1 text-xs text-slate-500">队列筛选优先显示 blocked、ready to send 和即将到期动作；筛选只影响视图，不会自动发送或改状态。</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <el-tag v-for="(count, status) in consoleData?.status_counts" :key="status" effect="plain">{{ status }}: {{ count }}</el-tag>
        </div>
      </div>
      <div class="mb-3 grid gap-3 lg:grid-cols-5">
        <el-select v-model="filters.status" clearable placeholder="状态筛选" @change="onStatusFilterChange">
          <el-option v-for="status in statusOptions" :key="status.value" :label="status.label" :value="status.value" />
        </el-select>
        <el-select v-model="filters.action_type" clearable placeholder="动作类型" @change="onExternalFilterChange">
          <el-option v-for="item in actionTypeOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-input v-model="filters.owner" clearable placeholder="负责人" @change="onExternalFilterChange" />
        <el-input v-model="filters.keyword" clearable placeholder="Partner / 依赖 / 下一步关键词" @change="onExternalFilterChange" />
        <div class="flex flex-wrap gap-2">
          <el-button size="small" type="primary" plain @click="onExternalFilterChange">应用筛选链接</el-button>
          <el-button size="small" type="danger" plain @click="applyStatusFilter('blocked')">只看阻塞</el-button>
          <el-button size="small" plain @click="resetFilters">清空</el-button>
        </div>
      </div>
      <div class="mb-2 text-xs text-slate-500">
        当前筛选：{{ activeExternalFilterLabel }}。URL 可分享；当前显示 {{ filteredActions.length }} / {{ actions.length }} 个动作；状态来自人工记录，不能替代真实外部回复或 sign-off。
      </div>
      <el-table :data="filteredActions" border size="small" empty-text="暂无匹配的外部执行动作">
        <el-table-column prop="action_type" label="Action type" min-width="180" />
        <el-table-column prop="target_partner_system" label="Target" min-width="180" />
        <el-table-column prop="owner" label="Owner" width="140">
          <template #default="{ row }">
            <el-input v-model="row.owner" size="small" @change="saveAction(row, { owner: row.owner })" />
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="Due date" width="150">
          <template #default="{ row }">
            <el-input v-model="row.due_date" size="small" placeholder="YYYY-MM-DD" @change="saveAction(row, { due_date: row.due_date })" />
          </template>
        </el-table-column>
        <el-table-column label="Status" width="190">
          <template #default="{ row }">
            <el-select v-model="row.status" size="small" @change="saveAction(row, editablePayload(row))">
              <el-option v-for="status in statusOptions" :key="status.value" :label="status.label" :value="status.value" />
            </el-select>
            <el-tag class="mt-1" :type="statusTagType(row.status)" effect="plain">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Dependency / Next step" min-width="300">
          <template #default="{ row }">
            <el-input v-model="row.dependency" type="textarea" :rows="2" placeholder="Dependency" @change="saveAction(row, { dependency: row.dependency })" />
            <el-input class="mt-2" v-model="row.next_step" type="textarea" :rows="2" placeholder="Next step" @change="saveAction(row, { next_step: row.next_step })" />
          </template>
        </el-table-column>
        <el-table-column label="Response / Risk / Notes" min-width="330">
          <template #default="{ row }">
            <el-input
              v-model="row.response_summary"
              type="textarea"
              :rows="2"
              placeholder="真实回复摘要；response received 必填"
              @change="saveAction(row, { response_summary: row.response_summary })"
            />
            <el-input class="mt-2" v-model="row.risk_notes" type="textarea" :rows="2" placeholder="Risk notes" @change="saveAction(row, { risk_notes: row.risk_notes })" />
            <el-input class="mt-2" v-model="row.notes" type="textarea" :rows="2" placeholder="Notes，不要粘贴 raw token" @change="saveAction(row, { notes: row.notes })" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openIntake(row)">回复录入</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-drawer v-model="intakeVisible" size="520px" title="真实回复安全录入">
      <div class="space-y-4">
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          title="只有用户贴出的真实回复才能标记 response received；不得把口头未确认内容写成 sign-off；raw token 只能记录为 PROVIDED_VIA_SECURE_CHANNEL。"
        />
        <div v-if="intakeAction" class="rounded border border-slate-200 bg-slate-50 p-3 text-sm">
          <div class="font-semibold text-slate-800">{{ intakeAction.action_type }}</div>
          <div class="mt-1 text-slate-600">{{ intakeAction.target_partner_system }}</div>
          <div class="mt-1 text-xs text-slate-500">当前状态：{{ intakeAction.status }} / 负责人：{{ intakeAction.owner || '未指定' }}</div>
        </div>
        <el-select v-model="intakeForm.status" class="w-full" placeholder="状态">
          <el-option v-for="status in statusOptions" :key="status.value" :label="status.label" :value="status.value" />
        </el-select>
        <el-input
          v-model="intakeForm.response_summary"
          type="textarea"
          :rows="4"
          placeholder="真实回复摘要；标记 response received 前必填。不要粘贴 token、报价成本、利润或供应商私密信息。"
        />
        <el-input v-model="intakeForm.risk_notes" type="textarea" :rows="3" placeholder="风险说明；区分 partner feedback、system issue、roadmap candidate。" />
        <el-input v-model="intakeForm.blocker_notes" type="textarea" :rows="3" placeholder="阻塞说明；如果 status=blocked，写清 owner / dependency / next step。" />
        <el-select v-model="intakeForm.redacted_credential_status" class="w-full" placeholder="脱敏凭证状态">
          <el-option v-for="item in redactedCredentialOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-input v-model="intakeForm.notes" type="textarea" :rows="3" placeholder="内部备注；不得包含 raw token、真实客户私密信息或未确认签字。" />
        <div class="flex justify-end gap-2">
          <el-button @click="intakeVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="saveIntake">保存录入</el-button>
        </div>
      </div>
    </el-drawer>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="font-semibold text-slate-800">Readiness Gap Intelligence</h3>
          <p class="mt-1 text-sm text-slate-600">
            把 staging、D9、pilot、partner rehearsal 的外部依赖转成可执行缺口：谁负责、下一步是什么、是否影响 D9 / pilot、需要哪类签字或凭证。
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <el-tag type="danger" effect="plain">P0 {{ readinessGapSummary.p0 }}</el-tag>
          <el-tag type="warning" effect="plain">D9 {{ readinessGapSummary.d9 }}</el-tag>
          <el-tag type="success" effect="plain">Pilot {{ readinessGapSummary.pilot }}</el-tag>
          <el-tag type="danger" effect="plain">Blocked {{ readinessGapSummary.blocked }}</el-tag>
        </div>
      </div>
      <el-table :data="readinessGaps" border size="small" empty-text="暂无 readiness gap">
        <el-table-column label="Gap / Impact" min-width="260">
          <template #default="{ row }">
            <div class="font-semibold text-slate-800">{{ row.title }}</div>
            <div class="mt-1 flex flex-wrap gap-1">
              <el-tag size="small" type="danger" effect="plain">{{ row.severity }}</el-tag>
              <el-tag size="small" effect="plain">{{ row.area }}</el-tag>
              <el-tag v-if="row.affects_d9" size="small" type="danger" effect="plain">影响 D9</el-tag>
              <el-tag v-if="row.affects_pilot" size="small" type="success" effect="plain">影响 Pilot</el-tag>
            </div>
            <p class="mt-1 text-xs text-slate-500">{{ row.gap_id }}</p>
          </template>
        </el-table-column>
        <el-table-column label="Owner / State" min-width="190">
          <template #default="{ row }">
            <div class="text-sm text-slate-700">{{ row.owner }}</div>
            <el-tag class="mt-1" effect="plain">{{ row.work_state }}</el-tag>
            <div v-if="row.source_action_statuses?.length" class="mt-1 flex flex-wrap gap-1">
              <el-tag v-for="status in row.source_action_statuses" :key="status" size="small" effect="plain">
                {{ status }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="下一步 / 阻塞原因" min-width="330">
          <template #default="{ row }">
            <p class="text-sm text-slate-700">{{ row.next_action }}</p>
            <p class="mt-2 text-xs text-slate-500">阻塞：{{ row.blocker_reason }}</p>
            <p class="mt-1 text-xs text-slate-500">证据：{{ row.evidence_required }}</p>
          </template>
        </el-table-column>
        <el-table-column label="依赖类型" min-width="220">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-tag v-if="row.needs_business_signoff" size="small" effect="plain">business sign-off</el-tag>
              <el-tag v-if="row.needs_security_signoff" size="small" effect="plain">security sign-off</el-tag>
              <el-tag v-if="row.needs_partner_feedback" size="small" effect="plain">partner feedback</el-tag>
              <el-tag v-if="row.needs_staging_credentials" size="small" effect="plain">staging credentials</el-tag>
            </div>
            <p class="mt-2 text-xs text-slate-500">{{ row.customer_safe_boundary }}</p>
          </template>
        </el-table-column>
        <el-table-column label="Partner / Product" min-width="260">
          <template #default="{ row }">
            <div class="text-sm font-medium text-slate-800">{{ row.partner_focus }}</div>
            <div class="mt-1 flex flex-wrap gap-1">
              <el-tag v-for="item in row.product_focus.slice(0, 8)" :key="item" size="small" effect="plain">{{ item }}</el-tag>
              <el-tag v-if="row.product_focus.length > 8" size="small" type="info" effect="plain">+{{ row.product_focus.length - 8 }}</el-tag>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 class="font-semibold text-slate-800">Staging / Pilot Readiness Gate</h3>
        <el-tag type="danger" effect="plain">D9 gate blocked</el-tag>
      </div>
      <div class="grid gap-3 md:grid-cols-3">
        <div v-for="row in stagingReadiness" :key="row.item" class="rounded border border-slate-100 bg-slate-50 p-3">
          <div class="text-sm font-semibold text-slate-800">{{ row.item }}</div>
          <el-tag class="my-2" type="warning" effect="plain">{{ row.status }}</el-tag>
          <p class="text-xs text-slate-600">{{ row.detail }}</p>
          <p v-if="row.next_action" class="mt-2 text-xs font-medium text-slate-700">下一步：{{ row.next_action }}</p>
          <div v-if="row.linked_action_statuses?.length" class="mt-2 flex flex-wrap gap-1">
            <el-tag v-for="status in row.linked_action_statuses" :key="status" size="small" effect="plain">
              action: {{ status }}
            </el-tag>
          </div>
          <p v-else class="mt-2 text-xs text-slate-400">尚未关联外部执行动作</p>
        </div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 class="font-semibold text-slate-800">HOSUN 升降系统字段边界</h3>
        <el-tag effect="plain">lifting systems / desk frames / desk legs / lifting columns / heavy-duty supply</el-tag>
      </div>
      <el-table :data="hosunFieldRows" border size="small">
        <el-table-column prop="field" label="Field" width="150" />
        <el-table-column prop="review_class" label="Review class" width="200">
          <template #default="{ row }">
            <el-tag effect="plain">{{ row.review_class }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rule" label="Rule" />
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
