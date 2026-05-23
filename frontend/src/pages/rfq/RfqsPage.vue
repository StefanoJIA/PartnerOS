<template>
  <div>
    <h2 class="mb-4 text-xl font-semibold text-slate-800">RFQs</h2>
    <el-form :inline="true" class="mb-4 flex flex-wrap gap-2" @submit.prevent="applyFilters">
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable placeholder="全部" class="w-44">
          <el-option v-for="s in RFQ_STATUSES" :key="s" :label="s" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item label="公司">
        <el-select v-model="filters.company_id" clearable filterable placeholder="全部" class="w-52">
          <el-option v-for="c in companies" :key="c.id" :label="c.company_name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="交期从">
        <el-date-picker v-model="filters.target_delivery_from" value-format="YYYY-MM-DD" class="w-36" />
      </el-form-item>
      <el-form-item label="至">
        <el-date-picker v-model="filters.target_delivery_to" value-format="YYYY-MM-DD" class="w-36" />
      </el-form-item>
      <el-form-item label="有报价">
        <el-select v-model="filters.has_quotation" clearable placeholder="不限" class="w-28">
          <el-option label="是" :value="true" />
          <el-option label="否" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item label="等伙伴报价">
        <el-switch v-model="filters.waiting_partner_quote" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit">筛选</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="rows" stripe v-loading="loading">
      <template #empty>
        <el-empty description="暂无 RFQ" />
      </template>
      <el-table-column label="#" width="140">
        <template #default="{ row }">
          <router-link class="text-blue-600 hover:underline" :to="{ name: 'rfq-detail', params: { rfqId: row.id } }">
            {{ row.rfq_number }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="company_name" label="公司" min-width="140" />
      <el-table-column prop="contact_label" label="联系人" width="120" />
      <el-table-column prop="lead_name" label="线索" min-width="120" />
      <el-table-column prop="status" label="状态" width="160" />
      <el-table-column prop="target_delivery_date" label="目标交期" width="120" />
      <el-table-column label="有报价" width="80">
        <template #default="{ row }">{{ row.has_quotation ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column prop="required_certifications" label="认证" min-width="120" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建" width="170" />
      <el-table-column prop="updated_at" label="更新" width="170" />
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
import { RFQ_STATUSES } from '@/constants/statusEnums'
const rows = ref<unknown[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const loading = ref(false)
const companies = ref<{ id: string; company_name: string }[]>([])

const filters = reactive({
  status: undefined as string | undefined,
  company_id: undefined as string | undefined,
  target_delivery_from: undefined as string | undefined,
  target_delivery_to: undefined as string | undefined,
  has_quotation: undefined as boolean | undefined,
  waiting_partner_quote: false,
})

async function loadCompanies() {
  const { data } = await http.get('/companies', { params: { page: 1, limit: 300 } })
  companies.value = data.items
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, limit: limit.value }
    if (filters.status) params.status = filters.status
    if (filters.company_id) params.company_id = filters.company_id
    if (filters.target_delivery_from) params.target_delivery_from = filters.target_delivery_from
    if (filters.target_delivery_to) params.target_delivery_to = filters.target_delivery_to
    if (filters.has_quotation !== undefined) params.has_quotation = filters.has_quotation
    if (filters.waiting_partner_quote) params.waiting_partner_quote = true
    const { data } = await http.get('/rfqs', { params })
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
  filters.company_id = undefined
  filters.target_delivery_from = undefined
  filters.target_delivery_to = undefined
  filters.has_quotation = undefined
  filters.waiting_partner_quote = false
  page.value = 1
  load()
}

onMounted(async () => {
  await loadCompanies()
  load()
})
</script>
