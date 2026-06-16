<template>
  <div class="space-y-5" v-loading="loading">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-900">今日运营决策队列</h2>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          把 readiness gap、外部执行、Market Response、Partner Onboarding、订单、反馈和收入机会汇成当天行动优先级。
        </p>
      </div>
      <div class="flex gap-2">
        <el-button size="small" type="primary" plain @click="go('/')">工作台</el-button>
        <el-button size="small" type="warning" plain @click="go('/external-execution')">外部执行</el-button>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="内部行动排序，不是外部确认：不自动发送、不记录 raw token、不声明真实 staging evidence、不自动改报价或订单状态。"
    />

    <section class="grid gap-3 xl:grid-cols-5">
      <div v-for="metric in metrics" :key="metric.label" class="rounded border border-slate-200 bg-white p-4">
        <div class="text-xs text-slate-500">{{ metric.label }}</div>
        <div class="mt-1 text-2xl font-semibold text-slate-900">{{ metric.value }}</div>
        <div class="mt-1 text-xs text-slate-500">{{ metric.help }}</div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="text-base font-semibold text-slate-900">今天先判断什么</h3>
          <p class="mt-1 text-sm text-slate-600">每条摘要都来自队列最高优先级项，用于决定当天站会或运营推进顺序。</p>
        </div>
        <el-tag effect="plain">{{ queue?.summary.status || 'READY_FOR_STAGING_HANDOFF' }}</el-tag>
      </div>
      <ol v-if="queue?.decision_brief.length" class="space-y-2">
        <li v-for="line in queue.decision_brief" :key="line" class="rounded bg-slate-50 p-3 text-sm text-slate-700">
          {{ line }}
        </li>
      </ol>
      <el-empty v-else description="暂无决策摘要" />
    </section>

    <section class="grid gap-4 xl:grid-cols-3">
      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 text-base font-semibold text-slate-900">Partner 优先级</h3>
        <RollupList :rows="queue?.partner_rollup || []" @open="go" />
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 text-base font-semibold text-slate-900">产品线优先级</h3>
        <RollupList :rows="queue?.product_rollup || []" @open="go" />
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 text-base font-semibold text-slate-900">流程来源</h3>
        <RollupList :rows="queue?.category_rollup || []" @open="go" />
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 class="text-base font-semibold text-slate-900">可执行队列</h3>
          <p class="mt-1 text-sm text-slate-600">优先看 P0/P1、影响 D9/Pilot、等待外部输入和 HOSUN/JOOBOO/future partner 相关项。</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <el-select v-model="filters.category" clearable placeholder="流程来源" size="small" style="width: 180px">
            <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="filters.partner" clearable placeholder="Partner / Account" size="small" style="width: 190px">
            <el-option v-for="item in partnerOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="filters.impact" clearable placeholder="影响范围" size="small" style="width: 170px">
            <el-option label="影响 D9" value="d9" />
            <el-option label="影响 Pilot" value="pilot" />
            <el-option label="需要外部输入" value="external" />
            <el-option label="Business sign-off" value="business" />
            <el-option label="Security sign-off" value="security" />
          </el-select>
        </div>
      </div>

      <el-table :data="filteredItems" border size="small" empty-text="暂无匹配的运营决策项">
        <el-table-column label="优先动作" min-width="300">
          <template #default="{ row }">
            <div class="font-semibold text-slate-900">{{ row.title }}</div>
            <div class="mt-1 flex flex-wrap gap-1">
              <el-tag size="small" :type="priorityType(row.priority)" effect="plain">{{ row.priority }}</el-tag>
              <el-tag size="small" effect="plain">{{ row.category }}</el-tag>
              <el-tag v-if="row.affects_d9" size="small" type="danger" effect="plain">D9</el-tag>
              <el-tag v-if="row.affects_pilot" size="small" type="success" effect="plain">Pilot</el-tag>
              <el-tag v-if="row.depends_on_external_input" size="small" type="warning" effect="plain">外部输入</el-tag>
            </div>
            <p class="mt-1 text-xs text-slate-500">{{ row.reason }}</p>
          </template>
        </el-table-column>
        <el-table-column label="对象" min-width="220">
          <template #default="{ row }">
            <div class="font-medium text-slate-800">{{ row.partner_focus || row.customer_or_account || '内部运营' }}</div>
            <div class="mt-1 flex flex-wrap gap-1">
              <el-tag v-for="item in row.product_focus.slice(0, 4)" :key="item" size="small" effect="plain">{{ item }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="下一步" min-width="340">
          <template #default="{ row }">
            <p class="text-sm text-slate-700">{{ row.next_action }}</p>
            <p v-if="row.customer_safe_boundary" class="mt-1 text-xs text-slate-500">{{ row.customer_safe_boundary }}</p>
            <div v-if="row.handling" class="mt-2 rounded bg-slate-50 p-2 text-xs text-slate-600">
              <span>{{ handlingLabel(row.handling.handling_status) }}</span>
              <span v-if="row.handling.owner"> / {{ row.handling.owner }}</span>
              <span v-if="row.handling.follow_up_date"> / follow-up {{ row.handling.follow_up_date }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="协作" width="240" fixed="right">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-button size="small" type="primary" plain @click="handle(row, 'acknowledge')">知晓</el-button>
              <el-button size="small" type="success" plain @click="handle(row, 'assign')">接手</el-button>
              <el-button size="small" type="warning" plain @click="handle(row, 'wait_external')">等外部</el-button>
              <el-button size="small" link type="primary" @click="go(row.source_path)">源对象</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElButton, ElEmpty, ElMessage, ElTag } from 'element-plus'
import {
  fetchDailyDecisionQueue,
  updateDailyQueueHandling,
  type DailyDecisionQueue,
  type DailyDecisionQueueItem,
  type DailyDecisionQueueRollup,
} from '@/api/dashboard'

const router = useRouter()
const loading = ref(false)
const queue = ref<DailyDecisionQueue | null>(null)
const filters = reactive({
  category: '',
  partner: '',
  impact: '',
})

const RollupList = defineComponent({
  name: 'RollupList',
  props: {
    rows: { type: Array<DailyDecisionQueueRollup>, required: true },
  },
  emits: ['open'],
  setup(props, { emit }) {
    return () =>
      props.rows.length
        ? h(
            'div',
            { class: 'space-y-2' },
            props.rows.slice(0, 8).map((row) =>
              h('div', { class: 'rounded border border-slate-100 bg-slate-50 p-3' }, [
                h('div', { class: 'flex items-start justify-between gap-2' }, [
                  h('div', { class: 'font-medium text-slate-900' }, row.label),
                  h(ElTag, { size: 'small', type: priorityType(row.top_priority), effect: 'plain' }, () => row.top_priority),
                ]),
                h('div', { class: 'mt-1 flex flex-wrap gap-1 text-xs text-slate-500' }, [
                  h('span', `总 ${row.total}`),
                  h('span', `P0 ${row.p0}`),
                  h('span', `P1 ${row.p1}`),
                  h('span', `D9 ${row.affects_d9}`),
                  h('span', `Pilot ${row.affects_pilot}`),
                  h('span', `外部 ${row.external_input_required}`),
                ]),
                h('p', { class: 'mt-2 text-xs text-slate-600' }, row.top_next_action),
                row.source_paths.length
                  ? h(
                      ElButton,
                      { size: 'small', link: true, type: 'primary', onClick: () => emit('open', row.source_paths[0]) },
                      () => '进入最高优先来源',
                    )
                  : null,
              ]),
            ),
          )
        : h(ElEmpty, { description: '暂无数据', imageSize: 56 })
  },
})

const metrics = computed(() => [
  { label: '总决策项', value: queue.value?.summary.total ?? 0, help: '跨模块派生的今日行动' },
  { label: 'P0 / P1', value: `${queue.value?.summary.p0 ?? 0} / ${queue.value?.summary.p1 ?? 0}`, help: '优先处理的高影响项' },
  { label: 'Staging / D9', value: queue.value?.summary.staging_or_d9 ?? 0, help: '影响 D9 gate 的缺口' },
  { label: 'Pilot', value: queue.value?.summary.pilot ?? 0, help: '影响 pilot readiness 的事项' },
  { label: '外部输入', value: queue.value?.summary.external_input_required ?? 0, help: '依赖 partner / business / security / credentials' },
])

const categoryOptions = computed(() => Array.from(new Set((queue.value?.items || []).map((row) => row.category))).sort())
const partnerOptions = computed(() =>
  Array.from(new Set((queue.value?.items || []).map((row) => row.partner_focus || row.customer_or_account || '内部运营'))).sort(),
)
const filteredItems = computed(() =>
  (queue.value?.items || []).filter((row) => {
    if (filters.category && row.category !== filters.category) return false
    if (filters.partner && (row.partner_focus || row.customer_or_account || '内部运营') !== filters.partner) return false
    if (filters.impact === 'd9' && !row.affects_d9) return false
    if (filters.impact === 'pilot' && !row.affects_pilot) return false
    if (filters.impact === 'external' && !row.depends_on_external_input) return false
    if (filters.impact === 'business' && !row.needs_business_signoff) return false
    if (filters.impact === 'security' && !row.needs_security_signoff) return false
    return true
  }),
)

function priorityType(priority: string) {
  if (priority === 'P0') return 'danger'
  if (priority === 'P1') return 'warning'
  return 'info'
}

function handlingLabel(status: string) {
  const labels: Record<string, string> = {
    new: '未处理',
    acknowledged: '已知晓',
    in_progress: '处理中',
    deferred: '已延期',
    blocked: '处理阻塞',
    waiting_external: '等待外部输入',
    decision_recorded: '已记录内部决策',
  }
  return labels[status] || status
}

function currentOwner() {
  return localStorage.getItem('partneros_email') || 'operator'
}

function go(path: string) {
  router.push(path)
}

async function handle(row: DailyDecisionQueueItem, action: string) {
  try {
    await updateDailyQueueHandling({
      queue_item_id: row.id,
      source_type: row.source_type,
      source_id: row.source_id,
      source_path: row.source_path,
      title: row.title,
      category: row.category,
      priority: row.priority,
      partner_focus: row.partner_focus,
      product_focus: row.product_focus,
      customer_or_account: row.customer_or_account,
      action,
      owner: action === 'assign' ? currentOwner() : (row.handling?.owner || null),
      internal_note:
        action === 'wait_external'
          ? '等待真实外部输入；未收到回复前不得标记 approved、complete 或 response received。'
          : undefined,
    })
    ElMessage.success('已保存内部处理记录')
    await load()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存处理记录失败')
  }
}

async function load() {
  loading.value = true
  try {
    queue.value = await fetchDailyDecisionQueue()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
