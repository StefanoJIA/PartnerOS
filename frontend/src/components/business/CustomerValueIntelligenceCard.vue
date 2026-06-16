<template>
  <el-card v-if="companyId" shadow="never" class="mb-4">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div>
          <span>客户价值智能</span>
          <span class="ml-2 text-xs text-slate-500">历史报价 / 成交额 / 转化 / 复购 / 服务负担 / 下一步</span>
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
          <p class="text-xs text-slate-500">客户价值分</p>
          <p class="font-semibold text-slate-900">{{ numberText(valueRow?.value_score) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">历史报价额</p>
          <p class="font-semibold text-slate-900">{{ money(valueRow?.historical_quote_amount) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">成交额</p>
          <p class="font-semibold text-slate-900">{{ money(valueRow?.won_order_amount) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">加权 Pipeline</p>
          <p class="font-semibold text-slate-900">{{ money(valueRow?.weighted_pipeline_amount) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">报价转订单</p>
          <p class="font-semibold text-slate-900">{{ percent(valueRow?.conversion_rate) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">复购信号</p>
          <p class="font-semibold text-slate-900">{{ numberText(valueRow?.repeat_business_count) }}</p>
        </div>
      </div>

      <div class="grid gap-3 md:grid-cols-3">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-xs text-slate-500">价值层级</p>
          <p class="mt-1 font-medium text-slate-900">{{ labelFor('value_tier', valueRow?.value_tier) }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-xs text-slate-500">商业质量</p>
          <p class="mt-1 font-medium text-slate-900">{{ labelFor('quality', commercialQuality?.tier) }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-xs text-slate-500">服务负担</p>
          <p class="mt-1 font-medium text-slate-900">{{ labelFor('burden', valueRow?.service_burden || commercialQuality?.service_burden) }}</p>
        </div>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <p class="mb-1 font-medium text-slate-700">Partner / 产品关注</p>
          <div class="flex flex-wrap gap-2">
            <el-tag v-for="item in partnerFocus" :key="`partner-${item}`" effect="plain">{{ item }}</el-tag>
            <el-tag v-for="item in productFocus" :key="`product-${item}`" type="success" effect="plain">{{ item }}</el-tag>
            <span v-if="!partnerFocus.length && !productFocus.length" class="text-xs text-slate-500">
              暂无 partner 或产品线证据，先把机会、报价、订单或反馈关联到该客户。
            </span>
          </div>
        </div>
        <div>
          <p class="mb-1 font-medium text-slate-700">客户决策因素</p>
          <div class="flex flex-wrap gap-2">
            <el-tag v-for="item in decisionFactors" :key="item" type="info" effect="plain">{{ item }}</el-tag>
            <span v-if="!decisionFactors.length" class="text-xs text-slate-500">
              暂无可复用决策因素，需从报价学习、订单交付和反馈中沉淀。
            </span>
          </div>
        </div>
      </div>

      <div v-if="activeRisks.length || managementAnswer" class="grid gap-3 md:grid-cols-2">
        <div>
          <p class="mb-1 font-medium text-slate-700">价值风险</p>
          <ul v-if="activeRisks.length" class="list-inside list-disc text-slate-600">
            <li v-for="item in activeRisks" :key="item">{{ item }}</li>
          </ul>
          <p v-else class="text-slate-600">{{ managementAnswer }}</p>
        </div>
        <div>
          <p class="mb-1 font-medium text-slate-700">收入来源判断</p>
          <div class="grid gap-2 text-slate-700">
            <p>未来收入信号：{{ labelFor('future', valueRow?.future_revenue_signal) }}</p>
            <p>项目规模：{{ labelFor('scale', valueRow?.project_scale) }}</p>
            <p>推荐价值：{{ labelFor('referral', valueRow?.referral_value) }}</p>
          </div>
        </div>
      </div>

      <div class="rounded border border-blue-100 bg-blue-50 p-3">
        <p class="font-medium text-slate-900">管理层判断</p>
        <p class="mt-1 text-slate-700">{{ recommendedReason }}</p>
        <div class="mt-2 grid gap-2 text-xs text-slate-600 md:grid-cols-4">
          <span>报价 {{ numberText(valueRow?.quote_count) }}</span>
          <span>订单 {{ numberText(valueRow?.order_count) }}</span>
          <span>机会 {{ numberText(valueRow?.opportunity_count) }}</span>
          <span>未解决反馈 {{ numberText(valueRow?.unresolved_feedback_count) }}</span>
        </div>
      </div>

      <el-alert
        type="warning"
        show-icon
        :closable="false"
        title="内部客户价值判断：只使用报价、订单、pipeline、复购、反馈和交付信号；不暴露成本、利润、pricing breakdown、供应商私密备注、raw token、内部评分或未审查客户备注。"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { fetchCustomerValueIntelligence, type CustomerValueIntelligence } from '@/api/dashboard'

const props = withDefaults(
  defineProps<{
    companyId?: string | null
    companyName?: string | null
  }>(),
  {
    companyId: null,
    companyName: null,
  },
)

const loading = ref(false)
const error = ref('')
const intelligence = ref<CustomerValueIntelligence | null>(null)

const valueRows = computed(() => [
  ...(intelligence.value?.items ?? []),
  ...(intelligence.value?.commercial_quality_leaders ?? []),
  ...(intelligence.value?.service_burden_accounts ?? []),
])

const valueRow = computed(() => {
  const exact = valueRows.value.find((row) => String(row.company_id || '') === props.companyId)
  if (exact) return exact
  const byPath = valueRows.value.find((row) => String(row.path || '').includes(`/companies/${props.companyId}`))
  if (byPath) return byPath
  const name = normalize(props.companyName)
  if (!name) return null
  return valueRows.value.find((row) => {
    const customer = normalize(row.customer_name)
    return customer.includes(name) || name.includes(customer)
  }) ?? null
})

const commercialQuality = computed(() => {
  const value = valueRow.value?.commercial_quality
  return isRecord(value) ? value : null
})

const partnerFocus = computed(() => toTextList(valueRow.value?.partner_focus).slice(0, 6))
const productFocus = computed(() => toTextList(valueRow.value?.product_focus).slice(0, 8))
const decisionFactors = computed(() => toTextList(valueRow.value?.customer_decision_factors).slice(0, 10))
const activeRisks = computed(() => toTextList(valueRow.value?.active_risks).slice(0, 6))

const managementAnswer = computed(() => String(commercialQuality.value?.management_answer || valueRow.value?.recommended_reason || ''))
const recommendedReason = computed(() =>
  String(valueRow.value?.recommended_reason || managementAnswer.value || '先补齐报价、订单、反馈和复购证据，再判断是否值得深度跟进。'),
)
const nextAction = computed(() =>
  String(valueRow.value?.next_action || '先把客户关联到机会、报价、订单、反馈或复购记录，再形成客户价值判断。'),
)

const priorityTag = computed(() => {
  const priority = String(valueRow.value?.priority || '')
  if (priority === 'P1') return { label: 'P1 深跟/风险优先', type: 'warning' as const }
  if (priority === 'P2') return { label: 'P2 补商业证据', type: 'primary' as const }
  if (priority === 'P3') return { label: 'P3 观察', type: 'info' as const }
  return { label: valueRow.value ? '已建档' : '待沉淀', type: 'info' as const }
})

async function load() {
  if (!props.companyId) return
  loading.value = true
  error.value = ''
  try {
    intelligence.value = await fetchCustomerValueIntelligence(80)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '客户价值智能加载失败'
    intelligence.value = null
  } finally {
    loading.value = false
  }
}

function toTextList(value: unknown) {
  if (Array.isArray(value)) return value.map(String).map((item) => item.trim()).filter(Boolean)
  if (typeof value === 'string' && value.trim()) {
    return value.split(/[;,/|，、\s]+/).map((item) => item.trim()).filter(Boolean)
  }
  return []
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}

function normalize(value: unknown) {
  return String(value ?? '').trim().toLowerCase()
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

function percent(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return '—'
  return `${Math.round(numeric * 100)}%`
}

function labelFor(kind: string, value: unknown) {
  const labels: Record<string, string> = {
    active_prospect: '活跃潜在客户',
    strategic_account: '战略客户',
    growth_account: '增长客户',
    early_signal: '早期信号',
    healthy_growth_account: '健康增长客户',
    commercially_promising_but_needs_follow_up: '有商业潜力，需继续跟进',
    value_at_risk: '客户价值存在风险',
    qualification_needed: '需要继续资格确认',
    clean_or_light_burden: '服务负担较轻',
    medium_service_burden: '中等服务负担',
    high_service_burden: '高服务负担',
    quote_reactivation: '报价重新激活',
    open_pipeline: '开放 pipeline',
    repeat_business: '复购机会',
    needs_relationship_proof: '需要关系和复购证据',
    mid_size_project: '中型项目',
    'mid-size project': '中型项目',
  }
  const key = String(value ?? '')
  return labels[key] || key || (kind === 'future' ? '暂无明确收入信号' : '待判断')
}

watch(() => [props.companyId, props.companyName], load, { immediate: true })
</script>
