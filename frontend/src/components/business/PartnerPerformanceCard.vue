<template>
  <el-card shadow="never" class="mb-4">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div>
          <span>Partner 绩效智能</span>
          <span class="ml-2 text-xs text-slate-500">报价支持 / 赢单 / 交付 / 反馈 / 试点分配</span>
        </div>
        <el-tag :type="priorityTag.type" size="small">{{ priorityTag.label }}</el-tag>
      </div>
    </template>

    <div v-if="loading" v-loading="true" style="min-height: 92px" />
    <el-alert v-else-if="error" type="warning" :title="error" show-icon :closable="false" />

    <div v-else class="space-y-4 text-sm">
      <el-alert type="info" show-icon :closable="false" :title="nextAction" />

      <div class="grid gap-3 md:grid-cols-6">
        <div>
          <p class="text-xs text-slate-500">报价支持</p>
          <p class="font-semibold text-slate-900">{{ metricNumber('quote_support_count', fallback.quoteCount) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">赢单率</p>
          <p class="font-semibold text-slate-900">{{ percent(metricValue('win_rate')) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">订单额</p>
          <p class="font-semibold text-slate-900">{{ money(metricValue('order_amount')) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">准时交付</p>
          <p class="font-semibold text-slate-900">{{ percent(metricValue('on_time_delivery_rate')) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">反馈问题</p>
          <p class="font-semibold text-slate-900">{{ metricNumber('feedback_issue_count', 0) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">分配得分</p>
          <p class="font-semibold text-slate-900">{{ metricNumber('allocation_score', null) }}</p>
        </div>
      </div>

      <div class="grid gap-3 md:grid-cols-3">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-xs text-slate-500">报价分配判断</p>
          <p class="mt-1 font-medium text-slate-900">{{ labelFor('allocation_fit', performanceRow?.allocation_fit) }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-xs text-slate-500">Pilot 判断</p>
          <p class="mt-1 font-medium text-slate-900">{{ labelFor('pilot_fit', performanceRow?.pilot_fit) }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-xs text-slate-500">绩效健康</p>
          <p class="mt-1 font-medium text-slate-900">{{ labelFor('health', performanceRow?.health) }}</p>
        </div>
      </div>

      <div>
        <p class="mb-1 font-medium text-slate-700">产品覆盖</p>
        <div class="flex flex-wrap gap-2">
          <el-tag v-for="item in productFocus" :key="item" effect="plain">{{ item }}</el-tag>
          <span v-if="!productFocus.length" class="text-xs text-slate-500">暂无产品线证据，先补产品关联、报价记录或交付反馈。</span>
        </div>
      </div>

      <div v-if="missingInputs.length || riskSignals.length" class="grid gap-3 md:grid-cols-2">
        <div>
          <p class="mb-1 font-medium text-slate-700">缺失输入</p>
          <ul class="list-inside list-disc text-slate-600">
            <li v-for="item in missingInputs" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div>
          <p class="mb-1 font-medium text-slate-700">风险信号</p>
          <ul class="list-inside list-disc text-slate-600">
            <li v-for="item in riskSignals" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>

      <el-table v-if="productLineRows.length" :data="productLineRows" size="small" stripe>
        <el-table-column prop="product_focus" label="产品线" min-width="160" show-overflow-tooltip />
        <el-table-column label="报价分配" min-width="160">
          <template #default="{ row }">{{ labelFor('allocation_fit', row.allocation_fit) }}</template>
        </el-table-column>
        <el-table-column label="Pilot" min-width="140">
          <template #default="{ row }">{{ labelFor('pilot_fit', row.pilot_fit) }}</template>
        </el-table-column>
        <el-table-column label="赢单率" width="100">
          <template #default="{ row }">{{ percent(row.win_rate) }}</template>
        </el-table-column>
        <el-table-column label="下一步" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">{{ actionText(row.next_action) }}</template>
        </el-table-column>
      </el-table>

      <el-alert
        type="warning"
        show-icon
        :closable="false"
        title="内部绩效判断：不自动发送外部消息、不改变报价或订单状态，不把成本、利润、供应商私密备注、内部评分或 raw token 暴露给客户。"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { fetchPartnerPerformanceIntelligence, type PartnerPerformanceIntelligence } from '@/api/dashboard'

const props = withDefaults(
  defineProps<{
    partnerId?: string | null
    partnerName?: string | null
    brandName?: string | null
    productKeywords?: string[]
    quoteCount?: number
    orderCount?: number
  }>(),
  {
    partnerId: null,
    partnerName: null,
    brandName: null,
    productKeywords: () => [],
    quoteCount: 0,
    orderCount: 0,
  },
)

const loading = ref(false)
const error = ref('')
const intelligence = ref<PartnerPerformanceIntelligence | null>(null)

const fallback = computed(() => ({
  quoteCount: props.quoteCount,
  orderCount: props.orderCount,
}))

const performanceRow = computed(() => {
  const rows = [
    ...(intelligence.value?.items ?? []),
    ...(intelligence.value?.top_investment_candidates ?? []),
    ...(intelligence.value?.quote_allocation_candidates ?? []),
    ...(intelligence.value?.pilot_candidates ?? []),
    ...(intelligence.value?.allocation_risks ?? []),
    ...(intelligence.value?.partner_scoreboard ?? []),
  ]
  const exact = rows.find((row) => String(row.partner_id || '') === props.partnerId)
  if (exact) return exact
  return rows.find((row) => matchesPartnerName(row.partner_name) || matchesPartnerName(row.partner_focus))
})

const productLineRows = computed(() =>
  (intelligence.value?.product_line_allocation ?? [])
    .filter((row) => {
      if (matchesPartnerName(row.partner_name)) return true
      const focus = normalize(row.product_focus)
      return productFocus.value.some((item) => focus.includes(normalize(item)) || normalize(item).includes(focus))
    })
    .slice(0, 6),
)

const productFocus = computed(() => {
  const rowFocus = toTextList(performanceRow.value?.product_focus)
  if (rowFocus.length) return rowFocus
  return [...new Set(props.productKeywords.filter(Boolean))].slice(0, 8)
})

const missingInputs = computed(() => toTextList(performanceRow.value?.missing_inputs).slice(0, 6))
const riskSignals = computed(() => toTextList(performanceRow.value?.risk_signals).slice(0, 6))

const priorityTag = computed(() => {
  const priority = String(performanceRow.value?.investment_priority || '')
  if (priority === 'P1') return { label: 'P1 投入/风险优先', type: 'warning' as const }
  if (priority === 'P2') return { label: 'P2 补证据', type: 'primary' as const }
  if (priority === 'P3') return { label: 'P3 观察', type: 'info' as const }
  if (fallback.value.quoteCount || fallback.value.orderCount) return { label: '待聚合', type: 'info' as const }
  return { label: '待沉淀', type: 'info' as const }
})

const nextAction = computed(() => {
  const row = performanceRow.value
  if (row?.next_allocation_action || row?.next_action || row?.recommended_action) {
    return actionText(row.next_allocation_action || row.next_action || row.recommended_action)
  }
  if (fallback.value.orderCount) return '已有订单证据：继续补生产、物流、反馈复盘，用于判断是否扩大 Partner 分配。'
  if (fallback.value.quoteCount) return '已有报价支持：补赢输原因、客户决策因素和转化结果，再判断是否扩大报价分配。'
  return '先沉淀产品覆盖、报价支持、交付能力和反馈记录，再用于 Partner 分配或 pilot 判断。'
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    intelligence.value = await fetchPartnerPerformanceIntelligence(120)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Partner 绩效智能加载失败'
    intelligence.value = null
  } finally {
    loading.value = false
  }
}

function matchesPartnerName(value: unknown) {
  const candidate = normalize(value)
  if (!candidate) return false
  const names = [props.partnerName, props.brandName].map(normalize).filter(Boolean)
  return names.some((name) => candidate.includes(name) || name.includes(candidate))
}

function metricValue(key: string) {
  return performanceRow.value?.[key]
}

function metricNumber(key: string, defaultValue: number | null) {
  const value = metricValue(key)
  if (value === null || value === undefined || value === '') return defaultValue === null ? '—' : String(defaultValue)
  const numeric = Number(value)
  return Number.isFinite(numeric) ? String(numeric) : String(value)
}

function money(value: unknown) {
  const numeric = Number(value ?? 0)
  if (!Number.isFinite(numeric) || numeric <= 0) return '—'
  return `$${numeric.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
}

function percent(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return '—'
  return `${Math.round(numeric * 100)}%`
}

function toTextList(value: unknown) {
  if (Array.isArray(value)) return value.map(String).filter(Boolean)
  if (typeof value === 'string' && value.trim()) return value.split(/[;,/|，、]/).map((item) => item.trim()).filter(Boolean)
  return []
}

function normalize(value: unknown) {
  return String(value ?? '').trim().toLowerCase()
}

function labelFor(kind: 'allocation_fit' | 'pilot_fit' | 'health', value: unknown) {
  const labels: Record<string, string> = {
    allocate_next_quotes: '可分配下一轮匹配报价',
    selective_quote_allocation: '选择性报价分配',
    hold_expansion_until_risk_review: '先暂停扩大分配并复核风险',
    complete_inputs_before_allocation: '补齐输入后再分配',
    exploratory_support_only: '仅用于探索性支持',
    pilot_candidate: '可作为 pilot 候选',
    needs_conversion_proof: '需要转化证据',
    pilot_risk: '存在 pilot 风险',
    needs_partner_inputs: '需要 Partner 输入',
    early_candidate: '早期候选',
    delivery_or_feedback_risk: '交付/反馈风险',
    proven_commercial_partner: '已验证商业 Partner',
    quote_support_needs_conversion: '报价支持需转化',
    capability_gap: '能力输入缺口',
    early_partner_candidate: '早期 Partner 候选',
  }
  const key = String(value || '')
  return labels[key] || (key ? `${kind}: ${key}` : '暂无证据')
}

function actionText(value: unknown) {
  const text = String(value || '')
  if (!text) return '暂无下一步。'
  const normalized = text.toLowerCase()
  if (normalized.includes('do not expand high-value allocation')) {
    return '先不要扩大高价值项目分配，先复核交付、反馈或 Partner 风险信号。'
  }
  if (normalized.includes('allocate the next matching quote')) {
    return '可分配下一轮匹配报价或 pilot 机会，同时持续跟踪交付和反馈。'
  }
  if (normalized.includes('use this partner selectively')) {
    return '选择性用于匹配报价，并先沉淀赢输学习后再扩大 pilot。'
  }
  if (normalized.includes('complete product, delivery, resource')) {
    return '先补齐产品、交付、资源和客户可见输入，再用于商业分配。'
  }
  if (normalized.includes('use only for exploratory quote support')) {
    return '仅用于探索性报价支持，先补转化、交付和反馈证据。'
  }
  if (normalized.includes('review delivery and feedback')) {
    return '先复核交付和反馈，再决定是否分配更多高价值项目。'
  }
  if (normalized.includes('benchmark for quote allocation')) {
    return '可作为报价分配、产品方向和复购规划的 benchmark。'
  }
  if (normalized.includes('review quote follow-up')) {
    return '复盘报价跟进和赢输因素，再扩大报价量。'
  }
  if (normalized.includes('capture quote support')) {
    return '先补报价支持、产品覆盖和交付证据，再进入商业判断。'
  }
  return text
}

watch(
  () => [props.partnerId, props.partnerName, props.brandName],
  () => load(),
  { immediate: true },
)
</script>
