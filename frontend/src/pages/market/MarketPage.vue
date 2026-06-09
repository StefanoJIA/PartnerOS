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
import { http } from '@/api/http'
import { fetchMarketResponseIntelligence, type MarketResponseIntelligence } from '@/api/marketResponse'
import { formatApiError } from '@/api/errors'

const route = useRoute()
const rows = ref<unknown[]>([])
const filterCompanyId = ref<string | null>(null)
const focusCategory = ref<string | null>(null)
const data = ref<MarketResponseIntelligence | null>(null)
const loading = ref(false)
const error = ref('')

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

onMounted(load)
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
