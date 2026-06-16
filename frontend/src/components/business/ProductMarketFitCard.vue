<template>
  <el-card shadow="never" class="mb-4">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div>
          <span>Product-Market Fit 智能</span>
          <span class="ml-2 text-xs text-slate-500">购买因素 / 赢输学习 / 项目经验 / 反馈风险</span>
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
          <p class="text-xs text-slate-500">机会</p>
          <p class="font-semibold text-slate-900">{{ evidenceNumber('opportunities') }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">报价</p>
          <p class="font-semibold text-slate-900">{{ evidenceNumber('quotes') }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">订单</p>
          <p class="font-semibold text-slate-900">{{ evidenceNumber('orders', fallback.orderCount) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">反馈</p>
          <p class="font-semibold text-slate-900">{{ evidenceNumber('feedback') }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">报价转订单</p>
          <p class="font-semibold text-slate-900">{{ percent(conversionValue('quote_to_order_rate')) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">订单金额</p>
          <p class="font-semibold text-slate-900">{{ money(commercialValue('order_amount')) }}</p>
        </div>
      </div>

      <div class="grid gap-3 md:grid-cols-3">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-xs text-slate-500">Fit 状态</p>
          <p class="mt-1 font-medium text-slate-900">{{ labelFor('fit_status', pmfRow?.fit_status) }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-xs text-slate-500">Partner 方向</p>
          <p class="mt-1 font-medium text-slate-900">{{ partnerFocus }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-xs text-slate-500">产品方向</p>
          <p class="mt-1 font-medium text-slate-900">{{ productFocus.join(' / ') || '暂无产品线证据' }}</p>
        </div>
      </div>

      <div>
        <p class="mb-1 font-medium text-slate-700">关键购买因素</p>
        <el-table v-if="buyingFactors.length" :data="buyingFactors" size="small" stripe>
          <el-table-column prop="factor" label="因素" min-width="140" />
          <el-table-column prop="evidence_count" label="证据" width="80" />
          <el-table-column prop="wins" label="赢单" width="80" />
          <el-table-column prop="losses" label="丢单" width="80" />
          <el-table-column prop="feedback" label="反馈" width="80" />
          <el-table-column label="状态" width="130">
            <template #default="{ row }">{{ labelFor('factor_status', row.status) }}</template>
          </el-table-column>
        </el-table>
        <p v-else class="text-xs text-slate-500">暂无购买因素证据，先从机会、报价学习、订单交付和反馈中沉淀真实原因。</p>
      </div>

      <div v-if="customerObjections.length || competitorSignals.length" class="grid gap-3 md:grid-cols-2">
        <div>
          <p class="mb-1 font-medium text-slate-700">客户异议 / 丢单原因</p>
          <ul class="list-inside list-disc text-slate-600">
            <li v-for="item in customerObjections" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div>
          <p class="mb-1 font-medium text-slate-700">竞争信号</p>
          <ul class="list-inside list-disc text-slate-600">
            <li v-for="item in competitorSignals" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>

      <div v-if="projectExperience.length">
        <p class="mb-1 font-medium text-slate-700">项目经验</p>
        <ul class="list-inside list-disc text-slate-600">
          <li v-for="item in projectExperience" :key="item">{{ item }}</li>
        </ul>
      </div>

      <div v-if="relatedRows.length">
        <p class="mb-1 font-medium text-slate-700">相近产品线 PMF 证据</p>
        <el-table :data="relatedRows" size="small" stripe>
          <el-table-column label="Partner" width="150">
            <template #default="{ row }">{{ row.partner_focus || 'future partner' }}</template>
          </el-table-column>
          <el-table-column label="产品线" min-width="190">
            <template #default="{ row }">{{ listText(row.product_focus) }}</template>
          </el-table-column>
          <el-table-column label="Fit" width="130">
            <template #default="{ row }">{{ labelFor('fit_status', row.fit_status) }}</template>
          </el-table-column>
          <el-table-column label="下一步" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">{{ actionText(row.next_action) }}</template>
          </el-table-column>
        </el-table>
      </div>

      <el-alert
        type="warning"
        show-icon
        :closable="false"
        title="内部 PMF 判断：客户可见技术声称仍需业务确认；不暴露成本、利润、供应商私密备注、内部评分、raw token 或未经审查的风险说明。"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { fetchProductMarketFitIntelligence, type ProductMarketFitIntelligence } from '@/api/dashboard'

const props = withDefaults(
  defineProps<{
    productName?: string | null
    partnerFocus?: string | null
    productKeywords?: string[]
    relatedOrderCount?: number
  }>(),
  {
    productName: null,
    partnerFocus: null,
    productKeywords: () => [],
    relatedOrderCount: 0,
  },
)

const loading = ref(false)
const error = ref('')
const intelligence = ref<ProductMarketFitIntelligence | null>(null)

const fallback = computed(() => ({
  orderCount: props.relatedOrderCount,
}))

const pmfRows = computed(() => [
  ...(intelligence.value?.items ?? []),
  ...(intelligence.value?.top_product_lines ?? []),
  ...(intelligence.value?.pilot_risk_product_lines ?? []),
])

const pmfRow = computed(() => {
  const rows = pmfRows.value
  return rows
    .filter((row) => domainCompatible(row))
    .filter((row) => matchesProduct(row.product_focus) || matchesText(row.product_focus, row.dimensions, row.next_action, row.partner_focus))
    .sort((a, b) => rowScore(b) - rowScore(a))[0]
})

const relatedRows = computed(() =>
  uniqueRows(pmfRows.value)
    .filter(
      (row) =>
        row !== pmfRow.value
        && domainCompatible(row)
        && (matchesProduct(row.product_focus) || matchesText(row.product_focus, row.dimensions, row.next_action, row.partner_focus)),
    )
    .slice(0, 6),
)

const partnerFocus = computed(() => String(pmfRow.value?.partner_focus || props.partnerFocus || 'future partner'))
const productFocus = computed(() => {
  const focus = toTextList(pmfRow.value?.product_focus)
  if (focus.length) return focus
  return [...new Set(props.productKeywords.filter(Boolean))].slice(0, 8)
})
const buyingFactors = computed(() => toRecordList(pmfRow.value?.buying_factors_ranked).slice(0, 8))
const customerObjections = computed(() => toTextList(pmfRow.value?.customer_objections).slice(0, 6))
const competitorSignals = computed(() => toTextList(pmfRow.value?.competitor_signals).slice(0, 6))
const projectExperience = computed(() => toTextList(pmfRow.value?.project_experience).slice(0, 6))

const priorityTag = computed(() => {
  const priority = String(pmfRow.value?.priority || '')
  if (priority === 'P1') return { label: 'P1 产品验证优先', type: 'warning' as const }
  if (priority === 'P2') return { label: 'P2 补购买因素', type: 'primary' as const }
  if (priority === 'P3') return { label: 'P3 观察', type: 'info' as const }
  if (props.relatedOrderCount) return { label: '待聚合', type: 'info' as const }
  return { label: '待沉淀', type: 'info' as const }
})

const nextAction = computed(() => {
  if (pmfRow.value?.next_action) return actionText(pmfRow.value.next_action)
  if (props.relatedOrderCount) return '已有订单证据：把生产、物流、反馈和复购信号回流为购买因素与项目经验。'
  return '先从机会、报价学习、订单交付和客户反馈中沉淀真实购买因素。'
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    intelligence.value = await fetchProductMarketFitIntelligence(120)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Product-Market Fit 智能加载失败'
    intelligence.value = null
  } finally {
    loading.value = false
  }
}

function evidenceNumber(key: string, defaultValue = 0) {
  const counts = (pmfRow.value?.evidence_counts as Record<string, unknown> | undefined) ?? {}
  const value = counts[key]
  if (value === null || value === undefined || value === '') return String(defaultValue)
  const numeric = Number(value)
  return Number.isFinite(numeric) ? String(numeric) : String(value)
}

function conversionValue(key: string) {
  const conversion = (pmfRow.value?.conversion_signal as Record<string, unknown> | undefined) ?? {}
  return conversion[key]
}

function commercialValue(key: string) {
  const commercial = (pmfRow.value?.commercial_value as Record<string, unknown> | undefined) ?? {}
  return commercial[key]
}

function matchesPartner(value: unknown) {
  const candidate = normalize(value)
  const partner = normalize(props.partnerFocus)
  if (!partner || !candidate) return false
  return candidate.includes(partner) || partner.includes(candidate)
}

function matchesProduct(value: unknown) {
  const focus = Array.isArray(value) ? value.map(normalize).join(' ') : normalize(value)
  const productName = normalize(props.productName)
  const keywords = props.productKeywords.map(normalize).filter(Boolean)
  if (productName && focus && (focus.includes(productName) || productName.includes(focus))) return true
  return keywords.some((keyword) => focus.includes(keyword) || keyword.includes(focus))
}

function matchesText(...values: unknown[]) {
  const text = values.map((value) => (Array.isArray(value) ? value.map(normalize).join(' ') : normalize(value))).join(' ')
  const productName = normalize(props.productName)
  const keywords = props.productKeywords.map(normalize).filter(Boolean)
  return (!!productName && text.includes(productName)) || keywords.some((keyword) => text.includes(keyword))
}

function uniqueRows(rows: Array<Record<string, unknown>>) {
  const seen = new Set<string>()
  return rows.filter((row) => {
    const key = `${row.partner_focus || ''}|${listText(row.product_focus)}|${row.fit_status || ''}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function rowScore(row: Record<string, unknown>) {
  const counts = (row.evidence_counts as Record<string, unknown> | undefined) ?? {}
  const commercial = (row.commercial_value as Record<string, unknown> | undefined) ?? {}
  let score = 0
  if (matchesPartner(row.partner_focus)) score += 80
  score += Number(counts.orders || 0) * 25
  score += Number(counts.wins || 0) * 20
  score += Number(counts.quotes || 0) * 8
  score += Number(counts.feedback || 0) * 8
  score += Number(counts.market_reviews || 0) * 6
  score += Number(commercial.order_amount || 0) > 0 ? 20 : 0
  if (row.priority === 'P1') score += 15
  if (row.fit_status === 'order_validated') score += 18
  if (row.fit_status === 'pilot_risk' || row.fit_status === 'conversion_risk') score += 12
  score += domainScore(row)
  return score
}

function productDomain() {
  const text = normalize(`${props.productName || ''} ${props.productKeywords.join(' ')}`)
  if (/education|school|classroom|learning|student|project furniture/.test(text)) return 'education'
  if (/lifting|desk|frame|leg|column|heavy/.test(text)) return 'lifting'
  return 'general'
}

function domainCompatible(row: Record<string, unknown>) {
  const domain = productDomain()
  if (domain === 'general') return true
  const text = normalize(`${row.partner_focus || ''} ${listText(row.product_focus)} ${listText(row.dimensions)}`)
  if (domain === 'education') {
    return /education|school|classroom|project furniture|jooboo|learning|student/.test(text)
  }
  if (domain === 'lifting') {
    return /lifting|desk|frame|leg|column|heavy|hosun/.test(text)
  }
  return true
}

function domainScore(row: Record<string, unknown>) {
  const domain = productDomain()
  const text = normalize(`${row.partner_focus || ''} ${listText(row.product_focus)} ${listText(row.dimensions)}`)
  if (domain === 'education') {
    let score = 0
    if (/jooboo/.test(text) && !/hosun/.test(text)) score += 260
    else if (/jooboo/.test(text) && /hosun/.test(text)) score += 80
    if (/education furniture|school|classroom|project furniture|learning/.test(text)) score += 110
    if (/lifting|column|desk frame|desk leg/.test(text)) score -= 40
    if (/hosun/.test(text) && !/jooboo|education|school|classroom|project furniture/.test(text)) score -= 180
    return score
  }
  if (domain === 'lifting') {
    let score = 0
    if (/hosun/.test(text) && !/jooboo/.test(text)) score += 260
    else if (/hosun/.test(text) && /jooboo/.test(text)) score += 80
    if (/lifting|desk|frame|leg|column|heavy/.test(text)) score += 110
    if (/education|school|classroom|project furniture/.test(text)) score -= 40
    if (/jooboo/.test(text) && !/hosun|lifting|desk|frame|leg|column/.test(text)) score -= 140
    return score
  }
  return 0
}

function toTextList(value: unknown) {
  if (Array.isArray(value)) return value.map(String).filter(Boolean)
  if (typeof value === 'string' && value.trim()) return value.split(/[;,/|，、]/).map((item) => item.trim()).filter(Boolean)
  return []
}

function toRecordList(value: unknown) {
  return Array.isArray(value) ? (value.filter((item) => item && typeof item === 'object') as Array<Record<string, unknown>>) : []
}

function listText(value: unknown) {
  const list = toTextList(value)
  return list.length ? list.join(' / ') : '—'
}

function normalize(value: unknown) {
  return String(value ?? '').trim().toLowerCase()
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

function labelFor(kind: 'fit_status' | 'factor_status', value: unknown) {
  const labels: Record<string, string> = {
    order_validated: '订单已验证',
    quote_learning_validated: '报价学习已验证',
    feedback_validated: '反馈已验证',
    market_review_needed: '需要市场复盘',
    market_learning: '市场学习中',
    customer_safe_preview: '客户可见预览候选',
    pilot_risk: 'Pilot 风险',
    conversion_risk: '转化风险',
    baseline_only: '只有基线，缺真实证据',
    early_signal: '早期信号',
    validated: '已验证',
    'needs evidence': '需要证据',
  }
  const key = String(value || '')
  return labels[key] || (key ? `${kind}: ${key}` : '暂无证据')
}

function actionText(value: unknown) {
  const text = String(value || '')
  if (!text) return '暂无下一步。'
  const normalized = text.toLowerCase()
  if (normalized.includes('capture opportunity, quote, order, and feedback evidence')) {
    return '先沉淀机会、报价、订单和反馈证据，再形成产品市场判断。'
  }
  if (normalized.includes('resolve delivery or after-sales evidence')) {
    return '先解决交付或售后证据问题，再把该产品线视为可复制。'
  }
  if (normalized.includes('review lost reasons and customer objections')) {
    return '先复盘丢单原因和客户异议，再扩大 Campaign 或报价量。'
  }
  if (normalized.includes('use won/order evidence')) {
    return '用赢单和订单证据优化报价定位、Partner 分配和复购目标。'
  }
  if (normalized.includes('connect quote learning and market response')) {
    return '把报价学习和 Market Response 复盘转成业务确认后的客户可见表述。'
  }
  if (normalized.includes('reuse customer-safe preview cautiously')) {
    return '谨慎复用客户可见预览，同时继续补报价、订单和反馈证据。'
  }
  if (normalized.includes('review delivery and feedback')) {
    return '先复核交付和反馈，再决定是否扩大该产品线。'
  }
  if (normalized.includes('business approval') || normalized.includes('customer-visible')) {
    return '客户可见表述需业务确认后再用于 Portal 或对外材料。'
  }
  if (normalized.includes('quote learning') || normalized.includes('win/loss')) {
    return '补充报价学习和赢输原因，用于下一轮报价策略。'
  }
  return text
}

watch(
  () => [props.productName, props.partnerFocus, props.productKeywords.join('|'), props.relatedOrderCount],
  () => load(),
  { immediate: true },
)
</script>
