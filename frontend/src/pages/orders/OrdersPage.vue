<template>
  <div>
    <h2 class="mb-4 text-xl font-semibold text-slate-800">Orders</h2>
    <el-form inline class="mb-4 flex flex-wrap gap-2" @submit.prevent="load">
      <el-form-item label="生产状态">
        <el-select v-model="filters.production_status" clearable placeholder="全部" class="!w-48">
          <el-option v-for="s in ORDER_PRODUCTION_STATUSES" :key="s" :label="s" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item label="海运状态">
        <el-select v-model="filters.shipping_status" clearable placeholder="全部" class="!w-48">
          <el-option v-for="s in ORDER_SHIPPING_STATUSES" :key="s" :label="s" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item label="风险">
        <el-select v-model="filters.risk_level" clearable placeholder="全部" class="!w-36">
          <el-option v-for="r in RISK_LEVELS" :key="r" :label="r" :value="r" />
        </el-select>
      </el-form-item>
      <el-form-item label="仅延误节点">
        <el-switch v-model="filters.delayed_only" />
      </el-form-item>
      <el-form-item label="公司">
        <el-select v-model="filters.company_id" clearable filterable placeholder="全部" class="!w-48">
          <el-option v-for="c in companyOptions" :key="c.id" :label="c.company_name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="制造伙伴">
        <el-select v-model="filters.manufacturing_partner_id" clearable filterable placeholder="全部" class="!w-48">
          <el-option v-for="x in partnerOptions" :key="x.id" :label="x.partner_name" :value="x.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit">筛选</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="rows" stripe v-loading="loading">
      <template #empty>
        <el-empty description="暂无订单，请调整筛选或创建订单" />
      </template>
      <el-table-column label="订单号" width="140">
        <template #default="{ row }">
          <router-link class="text-blue-600 hover:underline" :to="{ name: 'order-detail', params: { orderId: row.id } }">
            {{ row.order_number }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="company_name" label="公司" min-width="120" />
      <el-table-column prop="contact_label" label="联系人" width="120" />
      <el-table-column prop="lead_name" label="线索" width="120" />
      <el-table-column prop="rfq_number" label="RFQ" width="110" />
      <el-table-column prop="partner_name" label="制造伙伴" min-width="120" />
      <el-table-column prop="order_date" label="下单" width="110" />
      <el-table-column prop="target_delivery_date" label="目标交期" width="110" />
      <el-table-column prop="production_status" label="生产" width="120" />
      <el-table-column prop="shipping_status" label="海运" width="120" />
      <el-table-column prop="risk_level" label="风险" width="80" />
      <el-table-column prop="delayed_milestones_count" label="延误节点" width="90" />
      <el-table-column prop="total_amount" label="金额" width="90" />
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
import { ORDER_PRODUCTION_STATUSES, ORDER_SHIPPING_STATUSES, RISK_LEVELS } from '@/constants/statusEnums'

const rows = ref<unknown[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const loading = ref(false)

const filters = reactive({
  production_status: '',
  shipping_status: '',
  risk_level: '',
  delayed_only: false,
  company_id: '' as string,
  manufacturing_partner_id: '' as string,
})

const companyOptions = ref<{ id: string; company_name: string }[]>([])
const partnerOptions = ref<{ id: string; partner_name: string }[]>([])

async function loadMeta() {
  const [co, pa] = await Promise.all([
    http.get('/companies', { params: { page: 1, limit: 500 } }),
    http.get('/manufacturing-partners', { params: { page: 1, limit: 500 } }),
  ])
  companyOptions.value = co.data.items
  partnerOptions.value = pa.data.items
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, limit: limit.value }
    if (filters.production_status) params.production_status = filters.production_status
    if (filters.shipping_status) params.shipping_status = filters.shipping_status
    if (filters.risk_level) params.risk_level = filters.risk_level
    if (filters.delayed_only) params.delayed_only = true
    if (filters.company_id) params.company_id = filters.company_id
    if (filters.manufacturing_partner_id) params.manufacturing_partner_id = filters.manufacturing_partner_id
    const { data } = await http.get('/orders', { params })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadMeta()
  load()
})
</script>
