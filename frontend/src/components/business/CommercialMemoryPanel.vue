<template>
  <el-card v-if="companyId" shadow="never" class="mb-4">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <span>商业记忆 / Account 360</span>
          <p class="mt-1 text-xs text-slate-500">
            从客户视角聚合机会、报价、订单、反馈和赢输经验，帮助判断是否值得继续投入。
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <el-tag v-if="accountDetail" :type="priorityType(accountDetail.priority)" effect="plain">
            {{ accountDetail.priority || 'P2' }}
          </el-tag>
          <el-tag v-if="coverageSummary.total" type="primary" effect="plain">
            资产覆盖 {{ coverageSummary.covered }}/{{ coverageSummary.total }}
          </el-tag>
        </div>
      </div>
    </template>

    <div v-if="loading" v-loading="true" style="min-height: 140px" />
    <el-alert v-else-if="error" type="warning" :title="error" show-icon :closable="false" />

    <div v-else-if="accountDetail || valueDetail" class="space-y-4 text-sm">
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="内部商业记忆：只读聚合，不自动发送外部消息，不自动改变报价或订单状态，不展示成本、利润、供应商私密信息或 token。"
      />

      <div class="grid gap-3 lg:grid-cols-4">
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs text-slate-500">客户价值层级</p>
          <p class="mt-1 text-lg font-semibold text-slate-900">
            {{ textFrom(valueDetail?.summary, ['value_tier', 'customer_value_tier'], '待判断') }}
          </p>
          <p class="mt-1 text-xs text-slate-600">{{ valueDetail?.future_revenue_signal || '等待报价、订单或反馈形成收入判断。' }}</p>
        </div>
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs text-slate-500">加权潜在收入</p>
          <p class="mt-1 text-lg font-semibold text-slate-900">{{ money(numberFrom(valueDetail?.summary, ['weighted_pipeline_amount'])) }}</p>
          <p class="mt-1 text-xs text-slate-600">已赢订单 {{ money(numberFrom(valueDetail?.summary, ['won_order_amount'])) }}</p>
        </div>
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs text-slate-500">转化与复购信号</p>
          <p class="mt-1 text-lg font-semibold text-slate-900">
            {{ percent(numberFrom(valueDetail?.summary, ['quote_to_order_rate', 'conversion_rate'])) }}
          </p>
          <p class="mt-1 text-xs text-slate-600">{{ textFrom(accountDetail?.commercial_value, ['repeat_business_signal'], '复购信号待沉淀') }}</p>
        </div>
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs text-slate-500">项目规模 / 战略价值</p>
          <p class="mt-1 text-lg font-semibold text-slate-900">{{ valueDetail?.project_scale || '待判断' }}</p>
          <p class="mt-1 text-xs text-slate-600">{{ valueDetail?.strategic_value || '等待业务团队补充战略价值。' }}</p>
        </div>
      </div>

      <div class="rounded border border-blue-100 bg-blue-50 p-3">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p class="font-semibold text-slate-900">下一步商业动作</p>
            <p class="mt-1 text-sm text-slate-700">{{ nextCommercialAction }}</p>
          </div>
          <el-button
            v-if="sourcePaths.length"
            size="small"
            type="primary"
            plain
            @click="go(sourcePaths[0] || '')"
          >
            打开主要来源
          </el-button>
        </div>
        <div class="mt-2 flex flex-wrap gap-2">
          <el-tag v-for="partner in mergedPartners" :key="partner" effect="plain">{{ partner }}</el-tag>
          <el-tag v-for="product in mergedProducts.slice(0, 6)" :key="product" type="info" effect="plain">
            {{ product }}
          </el-tag>
        </div>
      </div>

      <div class="grid gap-3 lg:grid-cols-2">
        <div class="rounded border border-slate-100 p-3">
          <p class="font-semibold text-slate-900">为什么赢 / 为什么输</p>
          <p class="mt-1 text-xs text-slate-500">把报价和机会复盘转为下一次报价、Campaign 和产品沟通输入。</p>
          <div class="mt-2 grid gap-2">
            <div
              v-for="lesson in winLossLessons"
              :key="lesson"
              class="rounded bg-slate-50 p-2 text-xs text-slate-700"
            >
              {{ lesson }}
            </div>
            <p v-if="!winLossLessons.length" class="text-sm text-slate-500">暂无赢输复盘，下一次报价后应记录成交或丢单原因。</p>
          </div>
        </div>

        <div class="rounded border border-slate-100 p-3">
          <p class="font-semibold text-slate-900">客户决策因素与风险</p>
          <p class="mt-1 text-xs text-slate-500">用于判断当前客户是否值得继续投入，以及产品资料是否需要补强。</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <el-tag v-for="factor in valueDetail?.customer_decision_factors || []" :key="factor" type="success" effect="plain">
              {{ factor }}
            </el-tag>
            <el-tag v-for="risk in valueDetail?.active_risks || []" :key="risk" type="warning" effect="plain">
              {{ risk }}
            </el-tag>
          </div>
          <p v-if="!hasDecisionSignals" class="mt-2 text-sm text-slate-500">暂无明确决策因素或风险，应在报价、反馈或 Market Response 中继续沉淀。</p>
        </div>
      </div>

      <div class="rounded border border-slate-100 p-3">
        <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
          <div>
            <p class="font-semibold text-slate-900">商业资产证据链</p>
            <p class="mt-1 text-xs text-slate-500">管理层可直接看到该客户关联了哪些商业资产，而不是只看孤立公司资料。</p>
          </div>
          <el-tag type="primary" effect="plain">{{ evidenceRows.length }} 条证据</el-tag>
        </div>
        <el-table :data="evidenceRows.slice(0, 8)" size="small" border empty-text="暂无商业证据">
          <el-table-column prop="type" label="资产" width="110" />
          <el-table-column prop="title" label="对象" min-width="180" show-overflow-tooltip />
          <el-table-column prop="signal" label="商业信号" min-width="260" show-overflow-tooltip />
          <el-table-column label="打开" width="90">
            <template #default="{ row }">
              <el-button v-if="row.path" size="small" link type="primary" @click="go(row.path)">进入</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="rounded border border-slate-100 p-3">
        <p class="font-semibold text-slate-900">管理层问题</p>
        <div class="mt-2 grid gap-2 md:grid-cols-2">
          <div v-for="question in managementQuestionRows" :key="question.label" class="rounded bg-slate-50 p-2">
            <p class="text-xs font-medium text-slate-600">{{ question.label }}</p>
            <p class="mt-1 text-sm text-slate-800">{{ question.answer }}</p>
          </div>
        </div>
      </div>
    </div>

    <p v-else class="text-sm text-slate-500">
      暂无可聚合的报价、订单、反馈或机会。先把业务对象关联到公司，商业记忆会自动形成。
    </p>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  fetchAccount360Detail,
  fetchCustomerValueDetail,
  type Account360Detail,
  type CustomerValueDetail,
} from '@/api/dashboard'

const props = defineProps<{
  companyId?: string | null
  companyName?: string
}>()

type EvidenceRow = {
  type: string
  title: string
  signal: string
  path: string
}

const router = useRouter()
const loading = ref(false)
const error = ref('')
const accountDetail = ref<Account360Detail | null>(null)
const valueDetail = ref<CustomerValueDetail | null>(null)

const accountKey = computed(() => (props.companyId ? `company:${props.companyId}` : ''))

const coverageSummary = computed(() => {
  const coverage = accountDetail.value?.commercial_asset_coverage ?? {}
  const flags = Object.values(coverage).filter((value): value is boolean => typeof value === 'boolean')
  return {
    total: flags.length,
    covered: flags.filter(Boolean).length,
  }
})

const sourcePaths = computed<string[]>(() => {
  const paths = [
    ...(valueDetail.value?.source_paths ?? []),
    ...arrayFrom(accountDetail.value?.detail_summary?.source_paths),
    ...evidenceRows.value.map((row) => row.path),
  ].filter((path): path is string => typeof path === 'string' && Boolean(path))
  return Array.from(new Set(paths))
})

const mergedPartners = computed(() => {
  const partners = [
    ...(valueDetail.value?.partner_focus ?? []),
    ...(accountDetail.value?.partner_focus ?? []),
  ].map(String)
  return Array.from(new Set(partners)).filter(Boolean)
})

const mergedProducts = computed(() => {
  const products = [
    ...(valueDetail.value?.product_focus ?? []),
    ...(accountDetail.value?.product_focus ?? []),
  ].map(String)
  return Array.from(new Set(products)).filter(Boolean)
})

const nextCommercialAction = computed(() => {
  const motion = accountDetail.value?.next_commercial_motion
  return (
    textFrom(motion, ['next_action', 'recommended_action']) ||
    valueDetail.value?.next_action ||
    '先补齐客户价值、报价经验和反馈证据，再决定下一次商业动作。'
  )
})

const winLossLessons = computed(() => {
  const learning = valueDetail.value?.win_loss_learning
  return [
    ...arrayFrom(learning?.lessons),
    ...arrayFrom(learning?.quote_lessons),
    ...arrayFrom(learning?.loss_reasons),
    ...arrayFrom(learning?.win_reasons),
    ...arrayFrom(accountDetail.value?.commercial_questions?.why_win_or_lose),
  ].map(String).filter(Boolean).slice(0, 6)
})

const hasDecisionSignals = computed(() => {
  return Boolean(valueDetail.value?.customer_decision_factors?.length || valueDetail.value?.active_risks?.length)
})

const evidenceRows = computed<EvidenceRow[]>(() => {
  const rows: EvidenceRow[] = []
  for (const row of valueDetail.value?.opportunity_evidence ?? []) {
    rows.push(toEvidenceRow('机会', row))
  }
  for (const row of valueDetail.value?.quote_evidence ?? []) {
    rows.push(toEvidenceRow('报价', row))
  }
  for (const row of valueDetail.value?.order_evidence ?? []) {
    rows.push(toEvidenceRow('订单', row))
  }
  for (const row of valueDetail.value?.feedback_evidence ?? []) {
    rows.push(toEvidenceRow('反馈', row))
  }
  for (const row of accountDetail.value?.object_timeline ?? []) {
    rows.push(toEvidenceRow(textFrom(row, ['source_type', 'type'], '时间线'), row))
  }
  const seen = new Set<string>()
  return rows.filter((row) => {
    const key = `${row.type}:${row.title}:${row.path}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
})

const managementQuestionRows = computed(() => {
  const questions = valueDetail.value?.management_questions ?? {}
  const accountQuestions = accountDetail.value?.commercial_questions ?? {}
  return [
    {
      label: '谁最值得跟进',
      answer: textFrom(questions, ['who_to_follow', 'customer_value_answer'], props.companyName || valueDetail.value?.customer_name || '当前客户'),
    },
    {
      label: '为什么值得投入',
      answer: textFrom(questions, ['why_follow', 'investment_reason'], valueDetail.value?.future_revenue_signal || '等待更多商业证据。'),
    },
    {
      label: '什么因素影响成交',
      answer: textFrom(accountQuestions, ['what_converts', 'buying_factors'], valueDetail.value?.customer_decision_factors?.join(' / ') || '待沉淀'),
    },
    {
      label: '下一次如何复用经验',
      answer: textFrom(questions, ['next_quote_guidance', 'repeat_motion'], nextCommercialAction.value),
    },
  ]
})

function arrayFrom(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

function textFrom(source: unknown, keys: string[], fallback = '') {
  if (!source || typeof source !== 'object') return fallback
  const record = source as Record<string, unknown>
  for (const key of keys) {
    const value = record[key]
    if (Array.isArray(value)) {
      const text = value.map(String).filter(Boolean).join(' / ')
      if (text) return text
    }
    if (value !== null && value !== undefined && String(value).trim()) {
      return String(value)
    }
  }
  return fallback
}

function numberFrom(source: unknown, keys: string[]) {
  if (!source || typeof source !== 'object') return 0
  const record = source as Record<string, unknown>
  for (const key of keys) {
    const value = record[key]
    const parsed = typeof value === 'number' ? value : Number(value)
    if (Number.isFinite(parsed)) return parsed
  }
  return 0
}

function money(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value || 0)
}

function percent(value: number) {
  if (!Number.isFinite(value) || value <= 0) return '待判断'
  const normalized = value > 1 ? value : value * 100
  return `${Math.round(normalized)}%`
}

function priorityType(priority?: string) {
  if (priority === 'P0') return 'danger'
  if (priority === 'P1') return 'warning'
  if (priority === 'P2') return 'primary'
  return 'info'
}

function toEvidenceRow(type: string, row: Record<string, unknown>): EvidenceRow {
  return {
    type,
    title: textFrom(row, ['title', 'name', 'quote_number', 'order_number', 'opportunity_name', 'feedback_number', 'source_label'], '商业对象'),
    signal: textFrom(row, ['signal', 'current_signal', 'reason', 'commercial_lesson', 'next_action', 'status'], '等待更多商业信号。'),
    path: textFrom(row, ['path', 'source_path'], ''),
  }
}

function go(path: string) {
  if (path) router.push(path)
}

async function load() {
  if (!props.companyId) {
    accountDetail.value = null
    valueDetail.value = null
    return
  }
  loading.value = true
  error.value = ''
  try {
    const [account, value] = await Promise.allSettled([
      fetchAccount360Detail(accountKey.value),
      fetchCustomerValueDetail(props.companyId),
    ])
    accountDetail.value = account.status === 'fulfilled' ? account.value : null
    valueDetail.value = value.status === 'fulfilled' ? value.value : null
    if (!accountDetail.value && !valueDetail.value) {
      const reason = account.status === 'rejected' ? account.reason : value.status === 'rejected' ? value.reason : null
      throw reason instanceof Error ? reason : new Error('商业记忆加载失败')
    }
  } catch (err) {
    accountDetail.value = null
    valueDetail.value = null
    error.value = err instanceof Error ? err.message : '商业记忆加载失败'
  } finally {
    loading.value = false
  }
}

watch(() => props.companyId, load, { immediate: true })
</script>
