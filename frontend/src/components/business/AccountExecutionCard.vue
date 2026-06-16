<template>
  <el-card v-if="companyId" shadow="never" class="mb-4">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div>
          <span>{{ title }}</span>
          <span v-if="contextLabel" class="ml-2 text-xs text-slate-500">{{ contextLabel }}</span>
        </div>
        <el-tag v-if="accountExecution" :type="priorityTag(accountExecution.priority)" size="small">
          {{ accountExecution.priority || 'P2' }}
        </el-tag>
      </div>
    </template>

    <div v-if="loading" v-loading="true" style="min-height: 96px" />
    <el-alert v-else-if="error" type="warning" :title="error" show-icon :closable="false" />

    <div v-else-if="accountExecution" class="space-y-3 text-sm">
      <div class="grid gap-3 md:grid-cols-4">
        <div>
          <p class="text-xs text-slate-500">当前生命周期</p>
          <p class="font-semibold text-slate-900">{{ accountExecution.current_stage || '待判断' }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">负责人</p>
          <p class="font-semibold text-slate-900">{{ accountExecution.owner || 'operator' }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">Partner / 产品线</p>
          <p class="font-semibold text-slate-900">
            {{ accountExecution.partner_focus || '待识别' }} · {{ listText(accountExecution.product_focus) }}
          </p>
        </div>
        <div>
          <p class="text-xs text-slate-500">关联对象</p>
          <p class="font-semibold text-slate-900">{{ sourceCountsText(accountExecution.source_counts) }}</p>
        </div>
      </div>

      <div v-if="accountExecution.commercial_health" class="rounded border border-blue-100 bg-blue-50 p-3">
        <div class="mb-2 flex flex-wrap items-center gap-2">
          <el-tag :type="commercialHealthType(accountExecution.commercial_health.health)" effect="plain">
            {{ commercialHealthLabel(accountExecution.commercial_health.health) }}
          </el-tag>
          <el-tag effect="plain">{{ accountExecution.commercial_health.business_focus }}</el-tag>
          <el-tag type="info" effect="plain">商业健康 {{ accountExecution.commercial_health.score }}/100</el-tag>
        </div>
        <p class="text-sm font-medium text-slate-800">{{ accountExecution.commercial_health.next_best_action }}</p>
        <div class="mt-2 grid gap-2 text-xs text-slate-600 md:grid-cols-3">
          <p>{{ accountExecution.commercial_health.conversion_signal }}</p>
          <p>{{ accountExecution.commercial_health.delivery_signal }}</p>
          <p>{{ accountExecution.commercial_health.repeat_business_signal }}</p>
        </div>
        <p v-if="accountExecution.commercial_health.primary_risk" class="mt-2 text-xs text-rose-600">
          主要风险：{{ accountExecution.commercial_health.primary_risk }}
        </p>
      </div>

      <div v-if="accountExecution.stage_progression" class="rounded border border-emerald-100 bg-emerald-50 p-3">
        <div class="mb-2 flex flex-wrap items-center gap-2">
          <el-tag :type="stageProgressionType(accountExecution.stage_progression.health)" effect="plain">
            {{ stageProgressionLabel(accountExecution.stage_progression.health) }}
          </el-tag>
          <el-tag effect="plain">
            {{ accountExecution.stage_progression.current_stage }} → {{ accountExecution.stage_progression.next_stage || '复购维护' }}
          </el-tag>
          <el-tag type="info" effect="plain">{{ accountExecution.stage_progression.handoff_object }}</el-tag>
        </div>
        <p class="text-sm font-medium text-slate-800">{{ accountExecution.stage_progression.recommended_action }}</p>
        <p class="mt-1 text-xs text-slate-600">{{ accountExecution.stage_progression.why_now }}</p>
        <div v-if="accountExecution.stage_progression.missing_inputs?.length" class="mt-2 flex flex-wrap gap-2">
          <el-tag
            v-for="item in accountExecution.stage_progression.missing_inputs.slice(0, 5)"
            :key="item"
            size="small"
            type="warning"
            effect="plain"
          >
            {{ item }}
          </el-tag>
        </div>
        <el-button
          class="mt-2"
          size="small"
          type="success"
          plain
          @click="router.push(accountExecution.stage_progression.recommended_entry_path || accountExecution.active_paths?.[0] || '/')"
        >
          进入下一步
        </el-button>
      </div>

      <el-alert
        :title="String(accountExecution.next_action || '补齐下一步动作')"
        type="info"
        show-icon
        :closable="false"
      />

      <div class="rounded border border-indigo-100 bg-indigo-50 p-3">
        <div class="mb-2 flex flex-wrap items-start justify-between gap-2">
          <div>
            <p class="font-semibold text-slate-900">Account 360 商业档案</p>
            <p class="mt-1 text-xs text-slate-600">
              把 Lead、Opportunity、Quote、Order/Delivery、Feedback、Win/Loss、Repeat Business 汇到客户视角，用于判断下一次商业动作。
            </p>
          </div>
          <el-tag type="primary" effect="plain">完整度 {{ account360Summary.covered }}/{{ account360Summary.total }}</el-tag>
        </div>
        <div class="grid gap-2 md:grid-cols-3">
          <div v-for="asset in account360Assets" :key="asset.key" class="rounded bg-white p-2">
            <div class="flex items-center justify-between gap-2">
              <p class="text-sm font-medium text-slate-800">{{ asset.label }}</p>
              <el-tag size="small" :type="asset.count ? 'success' : 'info'" effect="plain">{{ asset.count }}</el-tag>
            </div>
            <p class="mt-1 min-h-8 text-xs text-slate-600">{{ asset.signal }}</p>
            <el-button v-if="asset.path" class="mt-1" size="small" link type="primary" @click="router.push(asset.path)">
              查看来源
            </el-button>
          </div>
        </div>
        <div class="mt-3 rounded bg-white p-2 text-xs text-slate-600">
          <span class="font-medium text-slate-800">下一商业动作：</span>
          {{ account360NextAction }}
        </div>
      </div>

      <div v-if="accountExecution.open_blockers?.length" class="rounded border border-amber-200 bg-amber-50 p-3">
        <p class="font-medium text-amber-900">当前阻塞</p>
        <ul class="mt-1 list-disc pl-5 text-amber-900">
          <li v-for="blocker in accountExecution.open_blockers" :key="blocker">{{ blocker }}</li>
        </ul>
      </div>
      <div class="flex flex-wrap gap-2">
        <el-tag v-for="impact in accountExecution.readiness_impact" :key="impact" effect="plain">{{ impact }}</el-tag>
      </div>

      <el-table v-if="accountLifecycle.length" :data="accountLifecycle" size="small" stripe>
        <el-table-column label="来源" width="110">
          <template #default="{ row }">{{ sourceLabel(row.source_type) }}</template>
        </el-table-column>
        <el-table-column prop="lifecycle_stage" label="阶段" width="120" />
        <el-table-column prop="current_signal" label="当前信号" min-width="220" show-overflow-tooltip />
        <el-table-column prop="next_action" label="下一步" min-width="220" show-overflow-tooltip />
        <el-table-column label="打开" width="90">
          <template #default="{ row }">
            <el-button v-if="row.path" link type="primary" @click="router.push(row.path)">进入</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <p v-else class="text-sm text-slate-500">
      暂无可聚合的线索、机会、报价、订单或反馈。先把业务对象关联到公司，账户主线会自动汇总。
    </p>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchCompanyWorkspace } from '@/api/objectWorkspaces'

interface AccountExecution {
  priority?: string
  current_stage?: string
  owner?: string
  partner_focus?: string
  product_focus?: string[]
  source_counts?: Record<string, number>
  active_paths?: string[]
  open_blockers?: string[]
  next_action?: string
  readiness_impact?: string[]
  commercial_health?: {
    health: string
    score: number
    business_focus: string
    primary_stage: string
    primary_source_type: string
    primary_source_id: string | null
    primary_path: string
    primary_risk: string | null
    next_best_action: string
    conversion_signal: string
    delivery_signal: string
    repeat_business_signal: string
    business_questions: string[]
    safety: Record<string, boolean>
  }
  stage_progression?: {
    health: string
    current_stage: string
    next_stage: string | null
    blocks_next_stage: boolean
    missing_inputs: string[]
    recommended_action: string
    handoff_object: string
    recommended_entry_path: string
    readiness_impact: string[]
    why_now: string
    safety: Record<string, boolean>
  }
}

interface AccountLifecycleRow {
  source_type?: string
  lifecycle_stage?: string
  current_signal?: string
  next_action?: string
  blocker?: string | null
  path?: string
}

type Account360Asset = {
  key: string
  label: string
  count: number
  signal: string
  path: string
}

const props = withDefaults(
  defineProps<{
    companyId?: string | null
    title?: string
    contextLabel?: string
  }>(),
  {
    title: '账户经营主线',
    contextLabel: '',
  },
)

const router = useRouter()
const loading = ref(false)
const error = ref('')
const workspace = ref<Record<string, unknown> | null>(null)

const businessExecution = computed(() => workspace.value?.business_execution as Record<string, unknown> | undefined)
const accountExecution = computed(() => (businessExecution.value?.account as AccountExecution | undefined) ?? null)
const accountLifecycle = computed(() => (businessExecution.value?.lifecycle as AccountLifecycleRow[]) ?? [])
const account360Assets = computed<Account360Asset[]>(() => {
  const rows = accountLifecycle.value
  const quoteRows = rows.filter((row) => row.source_type === 'quote')
  const feedbackRows = rows.filter((row) => row.source_type === 'feedback')
  return [
    buildAsset('lead', 'Lead / 客户开发', rows.filter((row) => row.source_type === 'lead'), '暂无关联线索。'),
    buildAsset('opportunity', 'Opportunity / 项目机会', rows.filter((row) => row.source_type === 'opportunity'), '暂无机会记录。'),
    buildAsset('quote', 'Quote / 报价经验', quoteRows, '暂无报价或报价学习。'),
    buildAsset('delivery', 'Order / Delivery', rows.filter((row) => row.source_type === 'order'), '暂无订单交付记录。'),
    buildAsset('feedback', 'Feedback / 售后反馈', feedbackRows, '暂无反馈记录。'),
    buildAsset('winloss', 'Win/Loss / Repeat', [...quoteRows, ...feedbackRows], '暂无赢输复盘或复购信号。'),
  ]
})
const account360Summary = computed(() => ({
  total: account360Assets.value.length,
  covered: account360Assets.value.filter((asset) => asset.count > 0).length,
}))
const account360NextAction = computed(() => {
  const stageAction = accountExecution.value?.stage_progression?.recommended_action
  const healthAction = accountExecution.value?.commercial_health?.next_best_action
  const explicitAction = accountExecution.value?.next_action
  return stageAction || healthAction || explicitAction || '补齐客户关联对象后再选择下一次商业动作。'
})

async function load() {
  if (!props.companyId) {
    workspace.value = null
    return
  }
  loading.value = true
  error.value = ''
  try {
    workspace.value = await fetchCompanyWorkspace(props.companyId)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '账户经营主线加载失败'
    workspace.value = null
  } finally {
    loading.value = false
  }
}

function listText(value: unknown) {
  return Array.isArray(value) && value.length ? value.map(String).join(' / ') : '待识别'
}

function sourceLabel(value: unknown) {
  const labels: Record<string, string> = {
    lead: '线索',
    opportunity: '机会',
    quote: '报价',
    order: '订单',
    feedback: '反馈',
  }
  const key = String(value ?? '')
  return labels[key] ?? key
}

function priorityTag(value: unknown) {
  const key = String(value ?? 'P2')
  if (key === 'P0') return 'danger'
  if (key === 'P1') return 'warning'
  if (key === 'P2') return 'primary'
  return 'info'
}

function commercialHealthLabel(value: unknown) {
  const labels: Record<string, string> = {
    conversion_ready: '成交推进',
    pipeline_active: '项目推进',
    delivery_risk: '交付风险',
    after_sales_attention: '售后维护',
    blocked: '推进阻塞',
    nurture: '继续培育',
  }
  const key = String(value ?? '')
  return labels[key] || key || '待判断'
}

function commercialHealthType(value: unknown) {
  const key = String(value ?? '')
  if (key === 'delivery_risk' || key === 'blocked') return 'danger'
  if (key === 'after_sales_attention') return 'warning'
  if (key === 'conversion_ready') return 'success'
  if (key === 'pipeline_active') return 'primary'
  return 'info'
}

function stageProgressionLabel(value: unknown) {
  const labels: Record<string, string> = {
    blocked: '阶段阻塞',
    needs_input: '需要补齐输入',
    ready_to_advance: '可推进下一阶段',
    repeat_business_ready: '复购维护',
  }
  const key = String(value ?? '')
  return labels[key] || key || '待判断'
}

function stageProgressionType(value: unknown) {
  const key = String(value ?? '')
  if (key === 'blocked') return 'danger'
  if (key === 'needs_input') return 'warning'
  if (key === 'ready_to_advance' || key === 'repeat_business_ready') return 'success'
  return 'info'
}

function sourceCountsText(value: unknown) {
  if (!value || typeof value !== 'object') return '暂无'
  const entries = Object.entries(value as Record<string, number>).filter(([, count]) => Number(count) > 0)
  return entries.length ? entries.map(([source, count]) => `${sourceLabel(source)} ${count}`).join(' · ') : '暂无'
}

function buildAsset(key: string, label: string, rows: AccountLifecycleRow[], fallback: string): Account360Asset {
  const top = rows[0]
  const blocker = rows.find((row) => row.blocker)?.blocker
  const signal = blocker || top?.current_signal || top?.next_action || fallback
  return {
    key,
    label,
    count: rows.length,
    signal,
    path: top?.path || '',
  }
}

watch(() => props.companyId, load, { immediate: true })
</script>
