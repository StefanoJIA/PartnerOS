<template>
  <el-card shadow="never" class="mb-4">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div>
          <span>{{ title }}</span>
          <span class="ml-2 text-xs text-slate-500">{{ subtitle }}</span>
        </div>
        <el-tag :type="impactPriority.type" size="small">{{ impactPriority.label }}</el-tag>
      </div>
    </template>

    <div v-if="loading" v-loading="true" style="min-height: 96px" />
    <el-alert v-else-if="error" type="warning" :title="error" show-icon :closable="false" />

    <div v-else class="space-y-4 text-sm">
      <div class="grid gap-3 md:grid-cols-5">
        <div>
          <p class="text-xs text-slate-500">机会</p>
          <p class="font-semibold text-slate-900">{{ matchedOpportunities.length }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">报价学习</p>
          <p class="font-semibold text-slate-900">{{ matchedQuotations.length }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">产品验证</p>
          <p class="font-semibold text-slate-900">{{ matchedProducts.length }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">Partner 判断</p>
          <p class="font-semibold text-slate-900">{{ matchedPartners.length }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-500">关联交付</p>
          <p class="font-semibold text-slate-900">{{ relatedOrderCount }}</p>
        </div>
      </div>

      <el-alert
        type="info"
        show-icon
        :closable="false"
        :title="nextDecision"
      />

      <div v-if="matchedProducts.length">
        <p class="mb-1 font-medium text-slate-700">产品验证 / Market Response</p>
        <el-table :data="matchedProducts" size="small" stripe>
          <el-table-column label="Partner" prop="partner_focus" width="120" />
          <el-table-column label="产品线" min-width="160">
            <template #default="{ row }">{{ listText(row.product_focus) }}</template>
          </el-table-column>
          <el-table-column label="验证维度" min-width="180">
            <template #default="{ row }">{{ listText(row.dimensions) }}</template>
          </el-table-column>
          <el-table-column prop="validation_signal" label="信号" min-width="220" show-overflow-tooltip />
          <el-table-column prop="next_action" label="下一步" min-width="220" show-overflow-tooltip />
        </el-table>
      </div>

      <div v-if="matchedOpportunities.length">
        <p class="mb-1 font-medium text-slate-700">项目机会</p>
        <el-table :data="matchedOpportunities" size="small" stripe>
          <el-table-column prop="opportunity_name" label="机会" min-width="180" show-overflow-tooltip />
          <el-table-column prop="probability" label="概率" width="80" />
          <el-table-column prop="decision_stage" label="阶段" width="120" />
          <el-table-column prop="risk" label="风险" min-width="220" show-overflow-tooltip />
          <el-table-column label="打开" width="90">
            <template #default="{ row }">
              <el-button link type="primary" @click="router.push(row.path)">进入</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="matchedQuotations.length">
        <p class="mb-1 font-medium text-slate-700">报价学习</p>
        <el-table :data="matchedQuotations" size="small" stripe>
          <el-table-column prop="quote_number" label="报价" width="140" />
          <el-table-column prop="status" label="状态" width="120" />
          <el-table-column prop="learning_signal" label="学习信号" min-width="220" show-overflow-tooltip />
          <el-table-column prop="next_action" label="下一步" min-width="220" show-overflow-tooltip />
          <el-table-column label="打开" width="90">
            <template #default="{ row }">
              <el-button link type="primary" @click="router.push(row.path)">进入</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="matchedPartners.length">
        <p class="mb-1 font-medium text-slate-700">Partner 能力判断</p>
        <el-table :data="matchedPartners" size="small" stripe>
          <el-table-column prop="partner_name" label="Partner" width="160" />
          <el-table-column prop="readiness_level" label="准备度" min-width="180" show-overflow-tooltip />
          <el-table-column prop="delivery_ability" label="交付能力" min-width="180" show-overflow-tooltip />
          <el-table-column prop="risk_assessment" label="风险" min-width="180" show-overflow-tooltip />
          <el-table-column prop="next_action" label="下一步" min-width="220" show-overflow-tooltip />
        </el-table>
      </div>

      <el-empty
        v-if="!hasMatchedSignal"
        description="暂无与当前产品或 Partner 直接匹配的机会、报价学习或市场验证信号。先从 Growth Operations、报价学习或 Market Response 沉淀真实业务信号。"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchBusinessExecution, type BusinessExecution } from '@/api/dashboard'

const props = withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    partnerFocus?: string | null
    productKeywords?: string[]
    relatedOrderCount?: number
  }>(),
  {
    title: '经营影响',
    subtitle: '机会 / 报价 / 产品验证 / Partner 能力',
    partnerFocus: null,
    productKeywords: () => [],
    relatedOrderCount: 0,
  },
)

const router = useRouter()
const loading = ref(false)
const error = ref('')
const execution = ref<BusinessExecution | null>(null)

const normalizedPartner = computed(() => normalize(props.partnerFocus))
const normalizedKeywords = computed(() => props.productKeywords.map(normalize).filter(Boolean))

const matchedOpportunities = computed(() =>
  (execution.value?.opportunities ?? []).filter((item) =>
    matchesPartner(item.partner_focus) || matchesKeywords(item.product_focus) || matchesText(item.opportunity_name, item.risk, item.next_action),
  ),
)
const matchedQuotations = computed(() =>
  (execution.value?.quotations ?? []).filter((item) =>
    matchesKeywords(item.product_focus) || matchesText(item.learning_signal, item.outcome_signal, item.next_action),
  ),
)
const matchedProducts = computed(() =>
  (execution.value?.products ?? []).filter((item) =>
    matchesPartner(item.partner_focus)
    || matchesKeywords(item.product_focus)
    || matchesKeywords(item.dimensions)
    || matchesText(item.validation_signal, item.risk, item.next_action),
  ),
)
const matchedPartners = computed(() =>
  (execution.value?.partners ?? []).filter((item) =>
    matchesPartner(item.partner_name)
    || matchesKeywords(item.product_coverage)
    || matchesText(item.readiness_level, item.delivery_ability, item.risk_assessment, item.next_action),
  ),
)

const hasMatchedSignal = computed(
  () =>
    matchedOpportunities.value.length > 0
    || matchedQuotations.value.length > 0
    || matchedProducts.value.length > 0
    || matchedPartners.value.length > 0
    || props.relatedOrderCount > 0,
)

const impactPriority = computed(() => {
  if (matchedOpportunities.value.some((item) => item.probability >= 70) || props.relatedOrderCount > 0) {
    return { label: 'P1', type: 'warning' as const }
  }
  if (hasMatchedSignal.value) return { label: 'P2', type: 'primary' as const }
  return { label: '待沉淀', type: 'info' as const }
})

const nextDecision = computed(() => {
  const productGap = matchedProducts.value.find((item) => /validation|sign-off|risk|gap|needs/i.test(`${item.risk} ${item.next_action}`))
  if (productGap) return productGap.next_action
  const opportunity = [...matchedOpportunities.value].sort((a, b) => b.probability - a.probability)[0]
  if (opportunity) return opportunity.next_action
  const quotation = matchedQuotations.value[0]
  if (quotation) return quotation.next_action
  const partner = matchedPartners.value[0]
  if (partner) return partner.next_action
  if (props.relatedOrderCount > 0) return '检查关联订单的生产、物流、反馈和复购风险，并把异常回流到 Market Response。'
  return '先从真实机会、报价学习、订单交付或客户反馈中沉淀可判断的经营信号。'
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    execution.value = await fetchBusinessExecution()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '经营影响加载失败'
    execution.value = null
  } finally {
    loading.value = false
  }
}

function normalize(value: unknown) {
  return String(value ?? '').trim().toLowerCase()
}

function matchesPartner(value: unknown) {
  const candidate = normalize(value)
  return !!normalizedPartner.value && !!candidate && (candidate.includes(normalizedPartner.value) || normalizedPartner.value.includes(candidate))
}

function matchesKeywords(values: unknown) {
  const joined = Array.isArray(values) ? values.map(normalize).join(' ') : normalize(values)
  return !!joined && normalizedKeywords.value.some((keyword) => joined.includes(keyword) || keyword.includes(joined))
}

function matchesText(...values: unknown[]) {
  const text = values.map(normalize).join(' ')
  return !!text && normalizedKeywords.value.some((keyword) => text.includes(keyword))
}

function listText(value: unknown) {
  return Array.isArray(value) && value.length ? value.map(String).join(' / ') : '—'
}

watch(
  () => [props.partnerFocus, props.productKeywords.join('|'), props.relatedOrderCount],
  load,
  { immediate: true },
)
</script>
