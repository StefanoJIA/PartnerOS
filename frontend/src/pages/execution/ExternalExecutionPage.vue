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

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const consoleData = ref<ExternalExecutionConsole | null>(null)

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

const statusType: Record<ExternalActionStatus, 'info' | 'primary' | 'warning' | 'success' | 'danger'> = {
  draft: 'info',
  'ready to send': 'primary',
  'sent manually': 'warning',
  'response received': 'success',
  blocked: 'danger',
  complete: 'success',
}

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
const hosunFieldRows = computed(() => consoleData.value?.lifting_systems_field_review || [])
const partnerCoverage = computed(() => consoleData.value?.partner_coverage || [])

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

function applyStatusFilter(status: ExternalActionStatus | '') {
  filters.status = status
  router.replace({ path: route.path, query: status ? { ...route.query, status } : { ...route.query, status: undefined } })
}

function onStatusFilterChange(value: string) {
  applyStatusFilter((value || '') as ExternalActionStatus | '')
}

function resetFilters() {
  filters.status = ''
  filters.action_type = ''
  filters.owner = ''
  filters.keyword = ''
  router.replace({ path: route.path, query: { ...route.query, status: undefined } })
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
  const status = typeof route.query.status === 'string' ? route.query.status : ''
  if (status) filters.status = status
  load()
})
watch(
  () => route.query.status,
  (status) => {
    filters.status = typeof status === 'string' ? status : ''
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
        <el-select v-model="filters.action_type" clearable placeholder="动作类型">
          <el-option v-for="item in actionTypeOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-input v-model="filters.owner" clearable placeholder="负责人" />
        <el-input v-model="filters.keyword" clearable placeholder="Partner / 依赖 / 下一步关键词" />
        <div class="flex flex-wrap gap-2">
          <el-button size="small" type="danger" plain @click="applyStatusFilter('blocked')">只看阻塞</el-button>
          <el-button size="small" plain @click="resetFilters">清空</el-button>
        </div>
      </div>
      <div class="mb-2 text-xs text-slate-500">
        当前显示 {{ filteredActions.length }} / {{ actions.length }} 个动作；状态来自人工记录，不能替代真实外部回复或 sign-off。
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
