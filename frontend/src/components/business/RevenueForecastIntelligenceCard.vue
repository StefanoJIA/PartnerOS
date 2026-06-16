<template>
  <el-card shadow="never" class="mb-4">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div>
          <span>Revenue Forecast Intelligence</span>
          <span class="ml-2 text-xs text-slate-500">未来收入 / 高概率项目 / 高风险收入 / Partner 与产品来源</span>
        </div>
        <el-tag :type="forecastTag.type" size="small">{{ forecastTag.label }}</el-tag>
      </div>
    </template>

    <div v-if="loading" v-loading="true" style="min-height: 96px" />
    <el-alert v-else-if="error" type="warning" :title="error" show-icon :closable="false" />

    <div v-else class="space-y-4 text-sm">
      <el-alert type="info" show-icon :closable="false" :title="nextAction" />

      <div class="grid gap-3 md:grid-cols-6">
        <div>
          <p class="text-xs text-slate-500">预测收入</p>
          <p class="font-semibold text-slate-900">{{ money(summary.total_forecast_amount) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">加权收入</p>
          <p class="font-semibold text-slate-900">{{ money(summary.total_weighted_amount) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">确认 Backlog</p>
          <p class="font-semibold text-slate-900">{{ money(summary.booked_backlog_amount) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">开放报价</p>
          <p class="font-semibold text-slate-900">{{ money(summary.open_quote_amount) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">高概率项目</p>
          <p class="font-semibold text-slate-900">{{ numberText(summary.high_probability_count) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">高风险收入</p>
          <p class="font-semibold text-slate-900">{{ money(summary.at_risk_weighted_amount) }}</p>
        </div>
      </div>

      <div class="grid gap-3 lg:grid-cols-[1.4fr_1fr]">
        <div>
          <p class="mb-1 font-medium text-slate-700">未来收入来源</p>
          <el-table v-if="forecastRows.length" :data="forecastRows" size="small" stripe>
            <el-table-column label="项目 / 客户" min-width="220">
              <template #default="{ row }">
                <div class="font-medium text-slate-900">{{ row.name || '未命名收入项目' }}</div>
                <div class="mt-1 text-xs text-slate-500">{{ row.customer_name || '未关联客户' }}</div>
              </template>
            </el-table-column>
            <el-table-column label="Partner / 产品" min-width="220">
              <template #default="{ row }">
                <div>{{ row.partner_focus || 'future partner' }}</div>
                <div class="mt-1 flex flex-wrap gap-1">
                  <el-tag v-for="item in toTextList(row.product_focus).slice(0, 4)" :key="item" size="small" effect="plain">
                    {{ item }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="概率 / 加权" width="150">
              <template #default="{ row }">
                <div>{{ numberText(row.probability) }}%</div>
                <div class="mt-1 text-xs text-slate-500">{{ money(row.weighted_amount) }}</div>
              </template>
            </el-table-column>
            <el-table-column label="风险 / 下一步" min-width="260">
              <template #default="{ row }">
                <el-tag size="small" :type="riskTag(row.risk_level)" effect="plain">{{ riskLabel(row.risk_level) }}</el-tag>
                <p class="mt-1 text-xs text-slate-600">{{ row.risk_reason || '暂无风险说明' }}</p>
                <p class="mt-1 text-xs text-slate-500">{{ row.next_action || '人工确认下一步推进动作。' }}</p>
              </template>
            </el-table-column>
          </el-table>
          <p v-else class="text-xs text-slate-500">
            暂无可预测收入。先把项目机会、报价或订单接入 Growth Operations，再形成收入预测。
          </p>
        </div>

        <div class="space-y-3">
          <div class="rounded border border-slate-200 p-3">
            <p class="mb-2 font-medium text-slate-700">收入桶</p>
            <div v-for="bucket in bucketMix" :key="String(bucket.name)" class="mb-2">
              <div class="flex items-center justify-between gap-2">
                <span>{{ bucketLabel(bucket.name) }}</span>
                <span class="font-medium">{{ money(bucket.weighted_amount) }}</span>
              </div>
              <p class="text-xs text-slate-500">{{ numberText(bucket.item_count) }} 个项目 / 原始额 {{ money(bucket.amount) }}</p>
            </div>
            <p v-if="!bucketMix.length" class="text-xs text-slate-500">暂无收入桶数据。</p>
          </div>

          <div class="rounded border border-slate-200 p-3">
            <p class="mb-2 font-medium text-slate-700">Partner / 产品线来源</p>
            <div class="flex flex-wrap gap-2">
              <el-tag v-for="item in partnerSignals" :key="`partner-${item}`" effect="plain">{{ item }}</el-tag>
              <el-tag v-for="item in productSignals" :key="`product-${item}`" type="success" effect="plain">{{ item }}</el-tag>
            </div>
            <p v-if="!partnerSignals.length && !productSignals.length" class="mt-1 text-xs text-slate-500">
              暂无 partner 或产品线收入来源。
            </p>
          </div>

          <div class="rounded border border-blue-100 bg-blue-50 p-3">
            <p class="font-medium text-slate-900">管理层要回答的问题</p>
            <ul class="mt-1 list-inside list-disc text-slate-700">
              <li>未来收入主要来自：{{ futureSourceText }}</li>
              <li>最容易成交：{{ easiestToCloseText }}</li>
              <li>需要人工复核：{{ highRiskText }}</li>
            </ul>
          </div>
        </div>
      </div>

      <el-alert
        type="warning"
        show-icon
        :closable="false"
        title="内部收入预测：只使用 opportunity、quote、order 的金额、概率和状态；不自动发送外部消息，不修改报价或订单状态，不暴露成本、利润、pricing breakdown、供应商私密备注、raw token 或内部-only comments。"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { fetchRevenueForecastIntelligence, type RevenueForecastIntelligence } from '@/api/dashboard'

const props = withDefaults(
  defineProps<{
    limit?: number
    contextLabel?: string | null
  }>(),
  {
    limit: 80,
    contextLabel: null,
  },
)

const loading = ref(false)
const error = ref('')
const intelligence = ref<RevenueForecastIntelligence | null>(null)

const summary = computed(() => intelligence.value?.summary ?? {
  total_forecast_amount: 0,
  total_weighted_amount: 0,
  weighted_opportunity_amount: 0,
  open_quote_amount: 0,
  weighted_quote_amount: 0,
  booked_backlog_amount: 0,
  at_risk_weighted_amount: 0,
  item_count: 0,
  high_probability_count: 0,
  high_risk_count: 0,
  committed_backlog_amount: 0,
  forecastable_weighted_amount: 0,
  manual_follow_up_weighted_amount: 0,
  weak_signal_weighted_amount: 0,
  forecast_quality_score: 0,
})

const forecastRows = computed(() => {
  const rows = [
    ...(intelligence.value?.high_probability_projects ?? []),
    ...(intelligence.value?.high_risk_projects ?? []),
    ...(intelligence.value?.committed_backlog ?? []),
    ...(intelligence.value?.forecastable_revenue ?? []),
    ...(intelligence.value?.manual_follow_up_revenue ?? []),
    ...(intelligence.value?.forecast_items ?? []),
  ]
  return uniqueRows(rows)
    .sort((a, b) => rowPriority(b) - rowPriority(a))
    .slice(0, 8)
})

const bucketMix = computed(() => (intelligence.value?.revenue_bucket_mix ?? []).slice(0, 5))
const partnerSignals = computed(() =>
  (intelligence.value?.forecast_by_partner ?? [])
    .map((row) => String(row.partner_focus || row.partner_name || row.name || '').trim())
    .filter(Boolean)
    .slice(0, 5),
)
const productSignals = computed(() =>
  (intelligence.value?.forecast_by_product ?? [])
    .flatMap((row) => toTextList(row.product_focus || row.name))
    .filter(Boolean)
    .slice(0, 8),
)

const nextAction = computed(() =>
  String(intelligence.value?.next_action || '先把 opportunity、quote、order 连接起来，再判断未来收入来源和高风险项目。'),
)

const forecastTag = computed(() => {
  if (Number(summary.value.high_risk_count || 0) > 0) return { label: '有高风险收入', type: 'warning' as const }
  if (Number(summary.value.high_probability_count || 0) > 0) return { label: '有高概率项目', type: 'success' as const }
  if (Number(summary.value.item_count || 0) > 0) return { label: '预测已建档', type: 'primary' as const }
  return { label: '待沉淀收入证据', type: 'info' as const }
})

const futureSourceText = computed(() => {
  const sources = intelligence.value?.future_revenue_sources ?? []
  if (sources.length) return sources.slice(0, 3).join(' / ')
  const firstBucket = bucketMix.value[0]
  return firstBucket ? bucketLabel(firstBucket.name) : '暂无明确来源'
})

const easiestToCloseText = computed(() => {
  const row = forecastRows.value.find((item) => Number(item.probability || 0) >= 60)
  if (!row) return '暂无高概率项目'
  return `${row.name || row.customer_name || '未命名项目'} (${numberText(row.probability)}%)`
})

const highRiskText = computed(() => {
  const row = forecastRows.value.find((item) => String(item.risk_level || '') === 'high')
  if (!row) return Number(summary.value.at_risk_weighted_amount || 0) > 0 ? money(summary.value.at_risk_weighted_amount) : '暂无高风险收入'
  return `${row.name || row.customer_name || '未命名项目'}：${row.risk_reason || '需人工复核'}`
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    intelligence.value = await fetchRevenueForecastIntelligence(props.limit)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Revenue Forecast Intelligence 加载失败'
    intelligence.value = null
  } finally {
    loading.value = false
  }
}

function rowPriority(row: Record<string, unknown>) {
  const risk = String(row.risk_level || '')
  const probability = Number(row.probability || 0)
  const weighted = Number(row.weighted_amount || 0)
  let score = weighted
  if (risk === 'high') score += 1_000_000
  if (probability >= 80) score += 500_000
  if (String(row.source_type || '') === 'order_backlog') score += 250_000
  return score
}

function uniqueRows(rows: Array<Record<string, unknown>>) {
  const seen = new Set<string>()
  return rows.filter((row) => {
    const key = `${row.source_type || ''}|${row.source_id || ''}|${row.name || ''}|${row.weighted_amount || ''}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function toTextList(value: unknown) {
  if (Array.isArray(value)) return value.map(String).map((item) => item.trim()).filter(Boolean)
  if (typeof value === 'string' && value.trim()) {
    return value.split(/[;,/|，、\s]+/).map((item) => item.trim()).filter(Boolean)
  }
  return []
}

function numberText(value: unknown) {
  const numeric = Number(value ?? 0)
  return Number.isFinite(numeric) ? String(Math.round(numeric)) : '—'
}

function money(value: unknown) {
  const numeric = Number(value ?? 0)
  if (!Number.isFinite(numeric) || numeric <= 0) return '—'
  return `$${numeric.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
}

function riskLabel(value: unknown) {
  const key = String(value || '')
  const labels: Record<string, string> = {
    high: '高风险',
    medium: '中风险',
    low: '低风险',
  }
  return labels[key] || '待判断'
}

function riskTag(value: unknown) {
  const key = String(value || '')
  if (key === 'high') return 'danger'
  if (key === 'medium') return 'warning'
  if (key === 'low') return 'success'
  return 'info'
}

function bucketLabel(value: unknown) {
  const key = String(value || '')
  const labels: Record<string, string> = {
    committed_backlog: '确认订单 Backlog',
    forecastable_pipeline: '可预测 Pipeline',
    manual_quote_follow_up: '人工报价跟进',
    early_pipeline: '早期 Pipeline',
    weak_signal: '弱信号收入',
    at_risk: '风险收入',
  }
  return labels[key] || key || '未分类收入'
}

watch(() => props.limit, load, { immediate: true })
</script>
