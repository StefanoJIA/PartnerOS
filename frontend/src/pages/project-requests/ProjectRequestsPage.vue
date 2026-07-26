<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-semibold text-slate-800">项目需求工作台</h2>
      <el-button type="primary" @click="reload">刷新</el-button>
    </div>
    <p class="mb-4 text-sm text-slate-600">
      客户站点提交的项目需求/RFQ（非正式订单）。运营审核后可生成 Quote Input Contract 并转入报价流程。
    </p>

    <el-form :inline="true" class="mb-4 flex flex-wrap gap-2" @submit.prevent="applyFilters">
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable placeholder="全部" class="w-44">
          <el-option v-for="s in STATUSES" :key="s" :label="statusLabel(s)" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item label="优先级">
        <el-select v-model="filters.priority" clearable placeholder="全部" class="w-32">
          <el-option v-for="p in PRIORITIES" :key="p" :label="p" :value="p" />
        </el-select>
      </el-form-item>
      <el-form-item label="搜索">
        <el-input v-model="filters.q" clearable placeholder="参考号/客户/SKU" class="w-52" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit">筛选</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="rows" stripe v-loading="loading">
      <template #empty>
        <el-empty description="暂无项目需求" />
      </template>
      <el-table-column label="参考号" width="140">
        <template #default="{ row }">
          <router-link
            class="text-blue-600 hover:underline"
            :to="{ name: 'project-request-detail', params: { requestId: row.id } }"
          >
            {{ row.request_reference }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="customer_name" label="客户" min-width="120" />
      <el-table-column prop="company_name" label="公司" min-width="140" />
      <el-table-column prop="partner_code" label="伙伴" width="100" />
      <el-table-column prop="sku" label="SKU" width="120" show-overflow-tooltip />
      <el-table-column label="完整度" width="90">
        <template #default="{ row }">{{ row.completeness_pct ?? '—' }}%</template>
      </el-table-column>
      <el-table-column label="状态" width="140">
        <template #default="{ row }">{{ statusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="90" />
      <el-table-column prop="source" label="来源" width="110" />
      <el-table-column prop="submitted_at" label="提交时间" width="170" />
    </el-table>
    <el-pagination
      class="mt-4"
      background
      layout="prev, pager, next"
      :total="total"
      v-model:current-page="page"
      :page-size="limit"
      @current-change="load"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { http } from '@/api/http'

const STATUSES = ['submitted', 'triage', 'needs_information', 'quote_ready', 'converted', 'declined']
const PRIORITIES = ['low', 'normal', 'high', 'urgent']

const STATUS_LABELS: Record<string, string> = {
  submitted: '已提交',
  triage: '分拣中',
  needs_information: '待补充资料',
  quote_ready: '可报价',
  converted: '已转化',
  declined: '已拒绝',
}

function statusLabel(s: string) {
  return STATUS_LABELS[s] || s
}

const rows = ref<Record<string, unknown>[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const loading = ref(false)

const filters = reactive({
  status: undefined as string | undefined,
  priority: undefined as string | undefined,
  q: undefined as string | undefined,
})

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, limit: limit.value }
    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    if (filters.q) params.q = filters.q
    const { data } = await http.get('/project-requests', { params })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 1
  load()
}

function resetFilters() {
  filters.status = undefined
  filters.priority = undefined
  filters.q = undefined
  applyFilters()
}

function reload() {
  load()
}

onMounted(load)
</script>
