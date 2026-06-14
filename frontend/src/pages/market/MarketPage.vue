<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">市场响应智能</h2>
        <p v-if="filterCompanyId" class="mt-1 text-sm text-slate-600">
          公司筛选：<code class="rounded bg-slate-100 px-1">{{ filterCompanyId }}</code>
        </p>
        <p v-if="focusCategory" class="mt-1 text-sm text-slate-600">
          方向筛选：<code class="rounded bg-slate-100 px-1">{{ focusLabel(focusCategory) }}</code>
        </p>
      </div>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-alert
      v-if="data"
      class="border border-emerald-200"
      type="success"
      :closable="false"
      title="仅作为运营建议看板：不会通知客户或供应商，不执行 AI 自动动作，不修改报价或订单状态。"
    />
    <el-alert v-if="error" type="error" :closable="false" :title="error" />

    <div class="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
      <div v-for="metric in metrics" :key="metric.label" class="rounded border border-slate-200 bg-white p-4">
        <div class="text-xs uppercase text-slate-500">{{ metric.label }}</div>
        <div class="mt-2 text-2xl font-semibold text-slate-900">{{ metric.value }}</div>
      </div>
    </div>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">关注方向</h3>
        <el-tag :type="data?.summary.filtered_by_company ? 'success' : 'info'" effect="plain">
          {{ data?.summary.filtered_by_company ? '已按公司筛选' : '全部公司' }}
        </el-tag>
        <el-tag :type="data?.summary.filtered_by_focus ? 'success' : 'info'" effect="plain">
          {{ data?.summary.filtered_by_focus ? '已按方向筛选' : '全部方向' }}
        </el-tag>
      </div>
      <div class="flex flex-wrap gap-2">
        <el-tag
          v-for="item in focusCategoryItems"
          :key="item.key"
          :type="item.key === focusCategory ? 'success' : 'info'"
          effect="plain"
        >
          {{ focusLabel(item.key) }} {{ item.count }}
        </el-tag>
        <span v-if="!focusCategoryItems.length" class="text-sm text-slate-500">暂无方向信号</span>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="font-semibold text-slate-800">为什么运营需要关注</h3>
          <p class="mt-1 text-sm text-slate-600">
            市场响应把需求、订单转化、生产摩擦、物流风险和客户反馈组合成需要人工审查的 partner 与产品方向。
            它不会自动修改报价、订单或 partner 选择。
          </p>
        </div>
        <el-tag type="warning" effect="plain">仅建议</el-tag>
      </div>
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div v-for="item in signalExplanations" :key="item.title" class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-sm font-semibold text-slate-800">{{ item.title }}</p>
          <p class="mt-1 text-sm text-slate-600">{{ item.body }}</p>
        </div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="font-semibold text-slate-800">Partner 产品方向解释</h3>
          <p class="mt-1 text-sm text-slate-600">
            市场响应用于判断 HOSUN lifting systems、desk frames、desk legs、lifting columns、heavy-duty supply，
            以及 JOOBOO education furniture / project furniture 是否值得继续投入。信号来自订单、物流、生产延迟和客户反馈。
          </p>
        </div>
        <el-tag type="success" effect="plain">HOSUN / JOOBOO 平级</el-tag>
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-sm font-semibold text-slate-800">HOSUN lifting systems</p>
          <p class="mt-1 text-sm text-slate-600">
            重点看 desk frames、desk legs、lifting columns 和 heavy-duty supply 的报价、订单、物流风险与反馈。
          </p>
        </div>
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-sm font-semibold text-slate-800">JOOBOO education furniture</p>
          <p class="mt-1 text-sm text-slate-600">
            重点看 education furniture / project furniture 的项目制采购、交付风险和客户反馈回流。
          </p>
        </div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">AI 辅助建议</h3>
        <el-tag type="warning" effect="plain">需要人工审查</el-tag>
      </div>
      <el-table :data="data?.recommendations || []" stripe>
        <el-table-column prop="priority" label="优先级" width="110">
          <template #default="{ row }">
            <el-tag :type="priorityType(row.priority)" effect="plain">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="area" label="领域" width="150" />
        <el-table-column prop="recommendation" label="建议" min-width="320" />
        <el-table-column prop="evidence" label="依据" min-width="220" />
        <el-table-column label="自动化" width="130">
          <template #default="{ row }">
            <el-tag :type="row.auto_execute ? 'danger' : 'info'" effect="plain">
              {{ row.auto_execute ? '自动' : '人工' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <h3 class="mb-3 font-semibold text-slate-800">需求信号看板</h3>
      <el-table :data="demandRows" stripe>
        <el-table-column prop="category" label="分类" min-width="200" />
        <el-table-column prop="market_signal_count" label="市场" width="90" />
        <el-table-column prop="feedback_signal_count" label="反馈" width="100" />
        <el-table-column prop="quote_line_count" label="报价" width="90" />
        <el-table-column prop="order_line_count" label="订单" width="90" />
        <el-table-column prop="quoted_quantity" label="报价数量" width="110" />
        <el-table-column prop="ordered_quantity" label="订单数量" width="115" />
        <el-table-column label="方向" width="185">
          <template #default="{ row }">
            <el-tag v-if="row.focus_category" type="success" effect="plain">{{ focusLabel(row.focus_category) }}</el-tag>
            <el-tag v-else-if="row.adjustable_frame_focus" type="success" effect="plain">升降桌架</el-tag>
            <span v-else class="text-slate-400">通用</span>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <div class="grid gap-5 xl:grid-cols-2">
      <section class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">反馈标签与摘要</h3>
        <el-table :data="data?.feedback.items || []" stripe>
          <el-table-column prop="ticket_number" label="工单" width="130" />
          <el-table-column prop="priority" label="优先级" width="100" />
          <el-table-column prop="subject" label="主题" min-width="220" />
          <el-table-column label="标签" min-width="220">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tag v-for="tag in row.tags" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">报价 / 订单转化</h3>
        <el-table :data="data?.win_loss.category_rows || []" stripe>
          <el-table-column prop="category" label="分类" min-width="180" />
          <el-table-column prop="quote_count" label="报价" width="90" />
          <el-table-column prop="order_count" label="订单" width="90" />
          <el-table-column prop="win_count" label="赢单" width="80" />
          <el-table-column prop="loss_count" label="丢单" width="90" />
          <el-table-column label="赢率" width="100">
            <template #default="{ row }">{{ formatRate(row.win_rate) }}</template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <section class="rounded border border-slate-200 bg-white p-4">
      <h3 class="mb-3 font-semibold text-slate-800">产品参数缺口</h3>
      <el-table :data="data?.product_gaps.items || []" stripe>
        <el-table-column prop="product_name" label="产品" min-width="240" />
        <el-table-column prop="category" label="分类" width="180" />
        <el-table-column prop="demand_signal_count" label="信号" width="90" />
        <el-table-column label="缺失字段" min-width="320">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-tag v-for="field in row.missing_fields" :key="field" size="small" type="warning" effect="plain">
                {{ field }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="font-semibold text-slate-800">Market Response 运营审查队列</h3>
          <p class="mt-1 text-sm text-slate-600">
            把 HOSUN 升降系统、JOOBOO 教育家具和 future partner 信号沉淀为人工审查项；这里只保存状态和下一步，不自动通知、不改报价/订单状态。
          </p>
        </div>
        <el-button :loading="reviewLoading" @click="loadReviews">刷新审查队列</el-button>
      </div>
      <el-alert
        v-if="reviewConsole"
        class="mb-3"
        type="warning"
        :closable="false"
        title="客户可见内容必须先过白名单：customer-safe candidate 不是 approved；needs validation/internal-only/pilot blocker 不得直接给客户看。"
      />
      <el-alert v-if="reviewError" class="mb-3" type="error" :closable="false" :title="reviewError" />

      <div class="mb-3 grid gap-3 lg:grid-cols-4">
        <el-select v-model="reviewFilters.partner_focus" clearable placeholder="Partner">
          <el-option label="HOSUN" value="HOSUN" />
          <el-option label="JOOBOO" value="JOOBOO" />
          <el-option label="future partner" value="future partner" />
        </el-select>
        <el-select v-model="reviewFilters.visibility_class" clearable placeholder="可见性分类">
          <el-option v-for="item in reviewConsole?.visibility_options || []" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="reviewFilters.status" clearable placeholder="审查状态">
          <el-option v-for="item in reviewConsole?.status_options || []" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button :loading="reviewLoading" type="primary" plain @click="loadReviews">应用筛选</el-button>
      </div>

      <el-table :data="reviewConsole?.reviews || []" stripe>
        <el-table-column prop="partner_focus" label="Partner" width="120" />
        <el-table-column prop="review_dimension_label" label="维度" width="130" />
        <el-table-column label="产品方向" min-width="220">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-tag v-for="item in row.product_focus" :key="item" size="small" effect="plain">{{ item }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="可见性" width="170">
          <template #default="{ row }">
            <el-select v-model="row.visibility_class" size="small" @change="saveReview(row, { visibility_class: row.visibility_class })">
              <el-option v-for="item in reviewConsole?.visibility_options || []" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-select v-model="row.status" size="small" @change="saveReview(row, { status: row.status })">
              <el-option v-for="item in reviewConsole?.status_options || []" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="120">
          <template #default="{ row }">
            <el-select v-model="row.priority" size="small" @change="saveReview(row, { priority: row.priority })">
              <el-option v-for="item in reviewConsole?.priority_options || []" :key="item.value" :label="item.value" :value="item.value" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="source_summary" label="信号摘要" min-width="320" />
        <el-table-column prop="next_action" label="下一步" min-width="260" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link type="primary" :loading="reviewSaving === row.id" @click="openReview(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-collapse class="mt-4">
        <el-collapse-item title="新增 / 编辑审查项" name="form">
          <div class="grid gap-3 lg:grid-cols-3">
            <el-input v-model="reviewForm.partner_focus" placeholder="Partner，例如 HOSUN / JOOBOO / future partner" />
            <el-input v-model="reviewForm.focus_category" placeholder="方向，例如 adjustable_desk_frames" />
            <el-select v-model="reviewForm.review_dimension" placeholder="审查维度">
              <el-option v-for="item in reviewConsole?.review_dimension_options || []" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="reviewForm.visibility_class" placeholder="可见性分类">
              <el-option v-for="item in reviewConsole?.visibility_options || []" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="reviewForm.priority" placeholder="优先级">
              <el-option v-for="item in reviewConsole?.priority_options || []" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="reviewForm.status" placeholder="状态">
              <el-option v-for="item in reviewConsole?.status_options || []" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>
          <div class="mt-3 grid gap-3 lg:grid-cols-2">
            <el-input v-model="reviewForm.product_focus_text" type="textarea" :rows="2" placeholder="产品方向，逗号分隔" />
            <el-input v-model="reviewForm.owner" placeholder="负责人" />
            <el-input v-model="reviewForm.source_summary" type="textarea" :rows="2" placeholder="信号摘要" />
            <el-input v-model="reviewForm.evidence_summary" type="textarea" :rows="2" placeholder="证据摘要" />
            <el-input v-model="reviewForm.customer_safe_summary" type="textarea" :rows="2" placeholder="客户可见摘要；仅候选文案，不代表 approved" />
            <el-input v-model="reviewForm.internal_notes" type="textarea" :rows="2" placeholder="内部备注；不得包含 raw token / 成本 / 利润 / 供应商私密信息" />
            <el-input v-model="reviewForm.next_action" type="textarea" :rows="2" placeholder="下一步" />
          </div>
          <div class="mt-3 flex gap-2">
            <el-button type="primary" :loading="reviewSaving === 'form'" @click="submitReviewForm">
              {{ reviewForm.id ? '保存审查项' : '新增审查项' }}
            </el-button>
            <el-button @click="resetReviewForm">清空</el-button>
          </div>
        </el-collapse-item>
      </el-collapse>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <h3 class="mb-3 font-semibold text-slate-800">市场情报来源</h3>
      <el-table :data="rows" stripe>
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="source_type" label="来源" width="120" />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { http } from '@/api/http'
import {
  createMarketResponseReview,
  fetchMarketResponseIntelligence,
  fetchMarketResponseReviews,
  updateMarketResponseReview,
  type MarketResponseIntelligence,
  type MarketResponseReview,
  type MarketResponseReviewConsole,
  type MarketResponseReviewPayload,
} from '@/api/marketResponse'
import { formatApiError } from '@/api/errors'

const route = useRoute()
const rows = ref<unknown[]>([])
const filterCompanyId = ref<string | null>(null)
const focusCategory = ref<string | null>(null)
const data = ref<MarketResponseIntelligence | null>(null)
const loading = ref(false)
const error = ref('')
const reviewConsole = ref<MarketResponseReviewConsole | null>(null)
const reviewLoading = ref(false)
const reviewSaving = ref<string | null>(null)
const reviewError = ref('')
const reviewFilters = ref({
  partner_focus: '',
  visibility_class: '',
  status: '',
})
const reviewForm = ref({
  id: '',
  partner_focus: 'HOSUN',
  focus_category: 'adjustable_desk_frames',
  product_focus_text: 'lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply',
  review_dimension: 'load',
  visibility_class: 'needs validation',
  priority: 'P1',
  status: 'needs review',
  source_type: 'operator review',
  source_summary: '',
  evidence_summary: '',
  customer_safe_summary: '',
  internal_notes: '',
  next_action: '',
  owner: '',
})

const metrics = computed(() => {
  const summary = data.value?.summary
  return [
    { label: '反馈', value: summary?.feedback_ticket_count ?? 0 },
    { label: '市场信号', value: summary?.market_signal_count ?? 0 },
    { label: '报价', value: summary?.quote_count ?? 0 },
    { label: '订单', value: summary?.order_count ?? 0 },
    { label: '产品缺口', value: summary?.product_gap_count ?? 0 },
    { label: '建议', value: summary?.recommendation_count ?? 0 },
  ]
})

function priorityType(priority: string) {
  if (priority === 'high') return 'danger'
  if (priority === 'medium') return 'warning'
  return 'info'
}

function formatRate(value: number | null) {
  if (value === null || value === undefined) return '暂无'
  return `${Math.round(value * 100)}%`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const companyId = typeof route.query.companyId === 'string' ? route.query.companyId : null
    const focus = typeof route.query.focus_category === 'string' ? route.query.focus_category : null
    filterCompanyId.value = companyId
    focusCategory.value = focus
    const params: { related_company_id?: string; focus_category?: string } = {}
    if (companyId) params.related_company_id = companyId
    if (focus) params.focus_category = focus
    const [intelligence, marketItems] = await Promise.all([
      fetchMarketResponseIntelligence(params),
      http.get('/market-intelligence', { params }),
    ])
    data.value = intelligence
    rows.value = marketItems.data.items
  } catch (e) {
    error.value = formatApiError(e, '市场响应智能加载失败。')
  } finally {
    loading.value = false
  }
}

function reviewQueryParams() {
  const params: { partner_focus?: string; visibility_class?: string; status?: string } = {}
  if (reviewFilters.value.partner_focus) params.partner_focus = reviewFilters.value.partner_focus
  if (reviewFilters.value.visibility_class) params.visibility_class = reviewFilters.value.visibility_class
  if (reviewFilters.value.status) params.status = reviewFilters.value.status
  return params
}

async function loadReviews() {
  reviewLoading.value = true
  reviewError.value = ''
  try {
    reviewConsole.value = await fetchMarketResponseReviews(reviewQueryParams())
  } catch (e) {
    reviewError.value = formatApiError(e, 'Market Response 审查队列加载失败。')
  } finally {
    reviewLoading.value = false
  }
}

function resetReviewForm() {
  reviewForm.value = {
    id: '',
    partner_focus: 'HOSUN',
    focus_category: 'adjustable_desk_frames',
    product_focus_text: 'lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply',
    review_dimension: 'load',
    visibility_class: 'needs validation',
    priority: 'P1',
    status: 'needs review',
    source_type: 'operator review',
    source_summary: '',
    evidence_summary: '',
    customer_safe_summary: '',
    internal_notes: '',
    next_action: '',
    owner: '',
  }
}

function openReview(row: MarketResponseReview) {
  reviewForm.value = {
    id: row.id,
    partner_focus: row.partner_focus,
    focus_category: row.focus_category,
    product_focus_text: row.product_focus.join(', '),
    review_dimension: row.review_dimension,
    visibility_class: row.visibility_class,
    priority: row.priority,
    status: row.status,
    source_type: row.source_type,
    source_summary: row.source_summary,
    evidence_summary: row.evidence_summary || '',
    customer_safe_summary: row.customer_safe_summary || '',
    internal_notes: row.internal_notes || '',
    next_action: row.next_action || '',
    owner: row.owner || '',
  }
}

function reviewPayloadFromForm(): MarketResponseReviewPayload {
  return {
    partner_focus: reviewForm.value.partner_focus,
    focus_category: reviewForm.value.focus_category,
    product_focus: reviewForm.value.product_focus_text
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean),
    review_dimension: reviewForm.value.review_dimension,
    visibility_class: reviewForm.value.visibility_class,
    priority: reviewForm.value.priority,
    status: reviewForm.value.status,
    source_type: reviewForm.value.source_type,
    source_summary: reviewForm.value.source_summary,
    evidence_summary: reviewForm.value.evidence_summary || null,
    customer_safe_summary: reviewForm.value.customer_safe_summary || null,
    internal_notes: reviewForm.value.internal_notes || null,
    next_action: reviewForm.value.next_action || null,
    owner: reviewForm.value.owner || null,
  }
}

async function submitReviewForm() {
  reviewSaving.value = 'form'
  reviewError.value = ''
  try {
    const payload = reviewPayloadFromForm()
    reviewConsole.value = reviewForm.value.id
      ? await updateMarketResponseReview(reviewForm.value.id, payload)
      : await createMarketResponseReview(payload)
    ElMessage.success('Market Response 审查项已保存')
    resetReviewForm()
  } catch (e) {
    reviewError.value = formatApiError(e, 'Market Response 审查项保存失败。')
  } finally {
    reviewSaving.value = null
  }
}

async function saveReview(row: MarketResponseReview, payload: Partial<MarketResponseReviewPayload>) {
  reviewSaving.value = row.id
  reviewError.value = ''
  try {
    reviewConsole.value = await updateMarketResponseReview(row.id, payload)
    ElMessage.success('审查状态已更新')
  } catch (e) {
    reviewError.value = formatApiError(e, '审查状态更新失败。')
    await loadReviews()
  } finally {
    reviewSaving.value = null
  }
}

onMounted(() => {
  load()
  loadReviews()
})
watch(() => [route.query.companyId, route.query.focus_category], load)

const focusCategoryItems = computed(() =>
  Object.entries(data.value?.summary.focus_category_counts || {}).map(([key, count]) => ({ key, count })),
)

const demandRows = computed(() => {
  const items = data.value?.demand.items || []
  if (!focusCategory.value || focusCategory.value === 'other') {
    return focusCategory.value === 'other' ? items.filter((item) => !item.focus_category) : items
  }
  return items.filter((item) => item.focus_category === focusCategory.value)
})

const signalExplanations = computed(() => {
  const summary = data.value?.summary
  return [
    {
      title: '需求匹配',
      body: `${summary?.quote_count ?? 0} 个报价和 ${summary?.order_count ?? 0} 个订单显示客户需求已经从浏览进入真实业务机会。`,
    },
    {
      title: '客户摩擦',
      body: `${summary?.feedback_ticket_count ?? 0} 个反馈工单暴露交付、质量、文件或预期差异，需要运营复核。`,
    },
    {
      title: '产品准备度',
      body: `${summary?.product_gap_count ?? 0} 个产品缺口说明仍有参数缺失，可能影响报价和 Portal 展示。`,
    },
    {
      title: 'Partner 方向',
      body: `${summary?.recommendation_count ?? 0} 条建议帮助运营判断哪些产品线或 partner playbook 值得关注。`,
    },
  ]
})

function focusLabel(key: string) {
  const labels: Record<string, string> = {
    adjustable_desk_frames: '升降桌架',
    desk_legs: '桌腿',
    lifting_columns: '升降柱',
    education_furniture: '教育家具',
    project_furniture: '项目制家具',
  }
  return labels[key] || key
}
</script>
