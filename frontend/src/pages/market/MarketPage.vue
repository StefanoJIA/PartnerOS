<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">Market response intelligence</h2>
        <p v-if="filterCompanyId" class="mt-1 text-sm text-slate-600">
          Company filter: <code class="rounded bg-slate-100 px-1">{{ filterCompanyId }}</code>
        </p>
      </div>
      <el-button :loading="loading" @click="load">Refresh</el-button>
    </div>

    <el-alert
      v-if="data"
      class="border border-emerald-200"
      type="success"
      :closable="false"
      title="Advisory board only: no customer notification, supplier notification, AI execution, quote status change, or order status change."
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
        <h3 class="font-semibold text-slate-800">Focus categories</h3>
        <el-tag :type="data?.summary.filtered_by_company ? 'success' : 'info'" effect="plain">
          {{ data?.summary.filtered_by_company ? 'company filtered' : 'all companies' }}
        </el-tag>
      </div>
      <div class="flex flex-wrap gap-2">
        <el-tag v-for="item in focusCategoryItems" :key="item.key" effect="plain">
          {{ focusLabel(item.key) }} {{ item.count }}
        </el-tag>
        <span v-if="!focusCategoryItems.length" class="text-sm text-slate-500">No focus-category signal yet</span>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">AI-assisted recommendations</h3>
        <el-tag type="warning" effect="plain">Human review required</el-tag>
      </div>
      <el-table :data="data?.recommendations || []" stripe>
        <el-table-column prop="priority" label="Priority" width="110">
          <template #default="{ row }">
            <el-tag :type="priorityType(row.priority)" effect="plain">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="area" label="Area" width="150" />
        <el-table-column prop="recommendation" label="Recommendation" min-width="320" />
        <el-table-column prop="evidence" label="Evidence" min-width="220" />
        <el-table-column label="Automation" width="130">
          <template #default="{ row }">
            <el-tag :type="row.auto_execute ? 'danger' : 'info'" effect="plain">
              {{ row.auto_execute ? 'Auto' : 'Manual' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <h3 class="mb-3 font-semibold text-slate-800">Demand signal board</h3>
      <el-table :data="data?.demand.items || []" stripe>
        <el-table-column prop="category" label="Category" min-width="200" />
        <el-table-column prop="market_signal_count" label="Market" width="90" />
        <el-table-column prop="feedback_signal_count" label="Feedback" width="100" />
        <el-table-column prop="quote_line_count" label="Quotes" width="90" />
        <el-table-column prop="order_line_count" label="Orders" width="90" />
        <el-table-column prop="quoted_quantity" label="Quoted qty" width="110" />
        <el-table-column prop="ordered_quantity" label="Ordered qty" width="115" />
        <el-table-column label="Focus" width="185">
          <template #default="{ row }">
            <el-tag v-if="row.focus_category" type="success" effect="plain">{{ focusLabel(row.focus_category) }}</el-tag>
            <el-tag v-else-if="row.adjustable_frame_focus" type="success" effect="plain">Adjustable frame</el-tag>
            <span v-else class="text-slate-400">General</span>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <div class="grid gap-5 xl:grid-cols-2">
      <section class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">Feedback tags and summaries</h3>
        <el-table :data="data?.feedback.items || []" stripe>
          <el-table-column prop="ticket_number" label="Ticket" width="130" />
          <el-table-column prop="priority" label="Priority" width="100" />
          <el-table-column prop="subject" label="Subject" min-width="220" />
          <el-table-column label="Tags" min-width="220">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tag v-for="tag in row.tags" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">Quote / order win-loss</h3>
        <el-table :data="data?.win_loss.category_rows || []" stripe>
          <el-table-column prop="category" label="Category" min-width="180" />
          <el-table-column prop="quote_count" label="Quotes" width="90" />
          <el-table-column prop="order_count" label="Orders" width="90" />
          <el-table-column prop="win_count" label="Wins" width="80" />
          <el-table-column prop="loss_count" label="Losses" width="90" />
          <el-table-column label="Win rate" width="100">
            <template #default="{ row }">{{ formatRate(row.win_rate) }}</template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <section class="rounded border border-slate-200 bg-white p-4">
      <h3 class="mb-3 font-semibold text-slate-800">Product parameter gaps</h3>
      <el-table :data="data?.product_gaps.items || []" stripe>
        <el-table-column prop="product_name" label="Product" min-width="240" />
        <el-table-column prop="category" label="Category" width="180" />
        <el-table-column prop="demand_signal_count" label="Signals" width="90" />
        <el-table-column label="Missing fields" min-width="320">
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
      <h3 class="mb-3 font-semibold text-slate-800">Source market intelligence items</h3>
      <el-table :data="rows" stripe>
        <el-table-column prop="title" label="Title" />
        <el-table-column prop="source_type" label="Source" width="120" />
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
const data = ref<MarketResponseIntelligence | null>(null)
const loading = ref(false)
const error = ref('')

const metrics = computed(() => {
  const summary = data.value?.summary
  return [
    { label: 'Feedback', value: summary?.feedback_ticket_count ?? 0 },
    { label: 'Market signals', value: summary?.market_signal_count ?? 0 },
    { label: 'Quotes', value: summary?.quote_count ?? 0 },
    { label: 'Orders', value: summary?.order_count ?? 0 },
    { label: 'Product gaps', value: summary?.product_gap_count ?? 0 },
    { label: 'Recommendations', value: summary?.recommendation_count ?? 0 },
  ]
})

function priorityType(priority: string) {
  if (priority === 'high') return 'danger'
  if (priority === 'medium') return 'warning'
  return 'info'
}

function formatRate(value: number | null) {
  if (value === null || value === undefined) return 'n/a'
  return `${Math.round(value * 100)}%`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const companyId = typeof route.query.companyId === 'string' ? route.query.companyId : null
    filterCompanyId.value = companyId
    const params = companyId ? { related_company_id: companyId } : {}
    const [intelligence, marketItems] = await Promise.all([
      fetchMarketResponseIntelligence(params),
      http.get('/market-intelligence', { params }),
    ])
    data.value = intelligence
    rows.value = marketItems.data.items
  } catch (e) {
    error.value = formatApiError(e, 'Failed to load market response intelligence.')
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.query.companyId, load)

const focusCategoryItems = computed(() =>
  Object.entries(data.value?.summary.focus_category_counts || {}).map(([key, count]) => ({ key, count })),
)

function focusLabel(key: string) {
  const labels: Record<string, string> = {
    adjustable_desk_frames: 'Adjustable frames',
    desk_legs: 'Desk legs',
    lifting_columns: 'Lifting columns',
    education_furniture: 'Education furniture',
    project_furniture: 'Project furniture',
  }
  return labels[key] || key
}
</script>
