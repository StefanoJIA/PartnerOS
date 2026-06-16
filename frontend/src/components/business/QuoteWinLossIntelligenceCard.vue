<template>
  <el-card shadow="never" class="mb-4">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div>
          <span>Win/Loss 商业经验库</span>
          <span class="ml-2 text-xs text-slate-500">成交原因 / 丢单原因 / 竞争信号 / 下一次报价指导</span>
        </div>
        <el-tag :type="priorityTag.type" size="small">{{ priorityTag.label }}</el-tag>
      </div>
    </template>

    <div v-if="loading" v-loading="true" style="min-height: 92px" />
    <el-alert v-else-if="error" type="warning" :title="error" show-icon :closable="false" />

    <div v-else class="space-y-4 text-sm">
      <el-alert type="info" show-icon :closable="false" :title="nextGuidance" />

      <div class="grid gap-3 md:grid-cols-5">
        <div>
          <p class="text-xs text-slate-500">匹配经验</p>
          <p class="font-semibold text-slate-900">{{ matchedRows.length }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">赢单</p>
          <p class="font-semibold text-slate-900">{{ outcomeCount('won') }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">丢单</p>
          <p class="font-semibold text-slate-900">{{ outcomeCount('lost') }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">经验胜率</p>
          <p class="font-semibold text-slate-900">{{ matchedWinRate }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">经验金额</p>
          <p class="font-semibold text-slate-900">{{ money(matchedAmount) }}</p>
        </div>
      </div>

      <div v-if="topFactors.length">
        <p class="mb-1 font-medium text-slate-700">常见决策因素</p>
        <div class="flex flex-wrap gap-2">
          <el-tag v-for="item in topFactors" :key="item" effect="plain">{{ item }}</el-tag>
        </div>
      </div>

      <el-table v-if="matchedRows.length" :data="matchedRows" size="small" stripe>
        <el-table-column label="结果" width="100">
          <template #default="{ row }">{{ outcomeLabel(row.outcome) }}</template>
        </el-table-column>
        <el-table-column label="客户 / 来源" min-width="180">
          <template #default="{ row }">
            <div class="font-medium text-slate-900">{{ row.customer || row.quote_number || row.opportunity_name || '商业经验' }}</div>
            <div class="text-xs text-slate-500">{{ sourceLabel(row.source_type) }} · {{ row.reason_category || '未分类' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="产品 / Partner" min-width="220">
          <template #default="{ row }">
            <div>{{ listText(row.product_focus) }}</div>
            <div class="text-xs text-slate-500">{{ row.partner_focus || 'future partner' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="commercial_lesson" label="商业经验" min-width="260" show-overflow-tooltip />
        <el-table-column label="下一次报价指导" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">{{ guidanceText(row.next_quote_guidance) }}</template>
        </el-table-column>
      </el-table>

      <el-empty
        v-else
        description="暂无与当前报价产品或 Partner 直接匹配的赢输经验。保存报价学习记录后，这里会形成可复用的商业经验。"
      />

      <div v-if="competitorSignals.length">
        <p class="mb-1 font-medium text-slate-700">竞争信号</p>
        <ul class="list-inside list-disc text-slate-600">
          <li v-for="item in competitorSignals" :key="item">{{ item }}</li>
        </ul>
      </div>

      <el-alert
        type="warning"
        show-icon
        :closable="false"
        title="内部 Win/Loss 经验：不自动发送外部消息、不改变报价或订单状态，不把成本、利润、供应商私密备注、内部评分、raw token 或未经审查的竞争/客户备注暴露给 Portal。"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { fetchWinLossIntelligenceDashboard, type WinLossIntelligenceDashboard } from '@/api/dashboard'

const props = withDefaults(
  defineProps<{
    quoteId?: string | null
    quoteNumber?: string | null
    customerName?: string | null
    partnerFocus?: string | null
    productKeywords?: string[]
  }>(),
  {
    quoteId: null,
    quoteNumber: null,
    customerName: null,
    partnerFocus: null,
    productKeywords: () => [],
  },
)

const loading = ref(false)
const error = ref('')
const dashboard = ref<WinLossIntelligenceDashboard | null>(null)

const matchedRows = computed(() =>
  (dashboard.value?.items ?? [])
    .filter((row) => isExactQuote(row) || matchesPartner(row.partner_focus) || matchesProduct(row.product_focus) || matchesText(row.decision_factors, row.commercial_lesson, row.next_quote_guidance))
    .sort((a, b) => rowScore(b) - rowScore(a))
    .slice(0, 8),
)

const competitorSignals = computed(() => {
  const fromRows = matchedRows.value
    .map((row) => String(row.competitor_signal || ''))
    .filter((item) => item && item !== 'competitor not recorded')
  const fallback = dashboard.value?.competitor_signals ?? []
  return [...new Set([...fromRows, ...fallback])].slice(0, 6)
})

const topFactors = computed(() => {
  const factors = matchedRows.value.flatMap((row) => toTextList(row.decision_factors))
  return [...new Set(factors.filter((item) => !/reason not recorded|competitor not recorded/i.test(item)))].slice(0, 10)
})

const matchedAmount = computed(() => matchedRows.value.reduce((sum, row) => sum + Number(row.commercial_amount || row.quote_value || row.estimated_value || 0), 0))

const matchedWinRate = computed(() => {
  const wins = outcomeCount('won')
  const losses = outcomeCount('lost')
  if (!wins && !losses) return '—'
  return `${Math.round((wins / (wins + losses)) * 100)}%`
})

const priorityTag = computed(() => {
  if (matchedRows.value.some((row) => row.outcome === 'lost')) return { label: '复核丢单经验', type: 'warning' as const }
  if (matchedRows.value.some((row) => row.outcome === 'won')) return { label: '复用赢单经验', type: 'success' as const }
  if (matchedRows.value.length) return { label: '经验待确认', type: 'primary' as const }
  return { label: '待沉淀', type: 'info' as const }
})

const nextGuidance = computed(() => {
  const exact = matchedRows.value.find((row) => isExactQuote(row))
  if (exact?.next_quote_guidance) return guidanceText(exact.next_quote_guidance)
  const lost = matchedRows.value.find((row) => row.outcome === 'lost')
  if (lost?.next_quote_guidance) return guidanceText(lost.next_quote_guidance)
  const won = matchedRows.value.find((row) => row.outcome === 'won')
  if (won?.next_quote_guidance) return guidanceText(won.next_quote_guidance)
  return '当前报价还缺少可复用的赢输经验；客户回复后请记录成交/丢单原因、竞争情况和决策因素。'
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    dashboard.value = await fetchWinLossIntelligenceDashboard(160)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Win/Loss 商业经验加载失败'
    dashboard.value = null
  } finally {
    loading.value = false
  }
}

function outcomeCount(outcome: string) {
  return matchedRows.value.filter((row) => row.outcome === outcome).length
}

function rowScore(row: Record<string, unknown>) {
  let score = 0
  if (isExactQuote(row)) score += 500
  if (matchesPartner(row.partner_focus)) score += 80
  if (matchesProduct(row.product_focus)) score += 120
  if (matchesText(row.decision_factors, row.commercial_lesson, row.next_quote_guidance)) score += 40
  if (row.outcome === 'lost') score += 20
  if (row.outcome === 'won') score += 15
  score += Math.min(Number(row.commercial_amount || row.quote_value || row.estimated_value || 0) / 1000, 100)
  return score
}

function isExactQuote(row: Record<string, unknown>) {
  if (props.quoteId && String(row.quote_id || '') === props.quoteId) return true
  if (props.quoteNumber && String(row.quote_number || '') === props.quoteNumber) return true
  return false
}

function matchesPartner(value: unknown) {
  const partner = normalize(props.partnerFocus)
  const candidate = normalize(value)
  if (!partner || !candidate) return false
  return candidate.includes(partner) || partner.includes(candidate)
}

function matchesProduct(value: unknown) {
  const focus = Array.isArray(value) ? value.map(normalize).join(' ') : normalize(value)
  return productKeywords().some((keyword) => focus.includes(keyword) || keyword.includes(focus))
}

function matchesText(...values: unknown[]) {
  const text = values.map((value) => (Array.isArray(value) ? value.map(normalize).join(' ') : normalize(value))).join(' ')
  return productKeywords().some((keyword) => text.includes(keyword))
}

function productKeywords() {
  return props.productKeywords
    .flatMap((value) => String(value || '').split(/[;,/|，、]/))
    .map(normalize)
    .filter((value) => value.length >= 3)
}

function normalize(value: unknown) {
  return String(value ?? '').trim().toLowerCase()
}

function toTextList(value: unknown) {
  if (Array.isArray(value)) return value.map(String).filter(Boolean)
  if (typeof value === 'string' && value.trim()) return value.split(/[;,/|，、]/).map((item) => item.trim()).filter(Boolean)
  return []
}

function listText(value: unknown) {
  const list = toTextList(value)
  return list.length ? list.join(' / ') : '—'
}

function money(value: unknown) {
  const numeric = Number(value ?? 0)
  if (!Number.isFinite(numeric) || numeric <= 0) return '—'
  return `$${numeric.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
}

function outcomeLabel(value: unknown) {
  const labels: Record<string, string> = {
    won: '赢单',
    lost: '丢单',
    no_decision: '暂无决策',
    on_hold: '暂停',
  }
  return labels[String(value || '')] || String(value || '未确认')
}

function sourceLabel(value: unknown) {
  const labels: Record<string, string> = {
    opportunity: '项目机会',
    quote_learning: '报价学习',
  }
  return labels[String(value || '')] || String(value || '来源')
}

function guidanceText(value: unknown) {
  const text = String(value || '')
  const normalized = text.toLowerCase()
  if (!text) return '暂无报价指导。'
  if (normalized.includes('use the winning reason')) return '复用赢单原因，更新下一次报价话术、产品证据和客户跟进重点。'
  if (normalized.includes('review lost reasons')) return '复盘丢单原因，先调整客户异议处理、竞争差异化和报价输入。'
  if (normalized.includes('capture competitor positioning')) return '记录竞争定位，并强化当前产品/Partner 的差异化表达。'
  if (normalized.includes('keep this outcome as internal learning')) return '先作为内部经验保留，等客户决策确认后再复用到报价策略。'
  if (normalized.includes('price')) return '复核价格解释和价值证据，避免下一轮报价只靠降价。'
  if (normalized.includes('delivery')) return '复核交期、物流和交付承诺，避免对外承诺未经确认。'
  return text
}

watch(
  () => [props.quoteId, props.quoteNumber, props.partnerFocus, props.productKeywords.join('|')],
  () => load(),
  { immediate: true },
)
</script>
