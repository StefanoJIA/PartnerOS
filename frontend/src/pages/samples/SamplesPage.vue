<template>
  <div>
    <h2 class="mb-4 text-xl font-semibold text-slate-800">Samples</h2>
    <el-form inline class="mb-4 flex flex-wrap gap-2" @submit.prevent="load">
      <el-form-item label="状态">
        <el-select v-model="filters.sample_status" clearable placeholder="全部" class="!w-44">
          <el-option v-for="s in SAMPLE_STATUSES" :key="s" :label="s" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item label="公司">
        <el-select v-model="filters.company_id" clearable filterable placeholder="全部" class="!w-48">
          <el-option v-for="c in companyOptions" :key="c.id" :label="c.company_name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="产品">
        <el-select v-model="filters.product_id" clearable filterable placeholder="全部" class="!w-48">
          <el-option v-for="p in productOptions" :key="p.id" :label="p.product_name" :value="p.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="制造伙伴">
        <el-select v-model="filters.manufacturing_partner_id" clearable filterable placeholder="全部" class="!w-48">
          <el-option v-for="x in partnerOptions" :key="x.id" :label="x.partner_name" :value="x.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="已签收无反馈">
        <el-switch v-model="filters.delivered_no_feedback" />
      </el-form-item>
      <el-form-item label="跟进到期">
        <el-switch v-model="filters.follow_up_due" />
      </el-form-item>
      <el-form-item label="已转订单">
        <el-select v-model="filters.converted_to_order" clearable placeholder="全部" class="!w-32">
          <el-option label="是" :value="true" />
          <el-option label="否" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit">筛选</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="rows" stripe v-loading="loading">
      <template #empty>
        <el-empty description="暂无样品记录" />
      </template>
      <el-table-column label="编号" width="150">
        <template #default="{ row }">
          <router-link class="text-blue-600 hover:underline" :to="{ name: 'sample-detail', params: { sampleId: row.id } }">
            {{ row.sample_request_number }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="company_name" label="公司" min-width="120" />
      <el-table-column prop="contact_label" label="联系人" width="120" />
      <el-table-column prop="lead_name" label="线索" width="120" />
      <el-table-column prop="rfq_number" label="RFQ" width="110" />
      <el-table-column prop="product_name" label="产品" min-width="120" />
      <el-table-column prop="partner_name" label="制造伙伴" min-width="120" />
      <el-table-column prop="sample_status" label="状态" width="130" />
      <el-table-column prop="courier" label="快递" width="90" />
      <el-table-column prop="tracking_number" label="运单" min-width="110" show-overflow-tooltip />
      <el-table-column prop="shipped_date" label="发货" width="110" />
      <el-table-column prop="delivered_date" label="签收" width="110" />
      <el-table-column prop="follow_up_due_date" label="跟进截止" width="110" />
      <el-table-column label="转订单" width="80">
        <template #default="{ row }">{{ row.converted_to_order ? '是' : '否' }}</template>
      </el-table-column>
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
import { SAMPLE_STATUSES } from '@/constants/statusEnums'
const rows = ref<unknown[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const loading = ref(false)

const filters = reactive({
  sample_status: '' as string,
  company_id: '' as string,
  product_id: '' as string,
  manufacturing_partner_id: '' as string,
  delivered_no_feedback: false,
  follow_up_due: false,
  converted_to_order: undefined as boolean | undefined,
})

const companyOptions = ref<{ id: string; company_name: string }[]>([])
const productOptions = ref<{ id: string; product_name: string }[]>([])
const partnerOptions = ref<{ id: string; partner_name: string }[]>([])

async function loadMeta() {
  const [co, pr, pa] = await Promise.all([
    http.get('/companies', { params: { page: 1, limit: 500 } }),
    http.get('/products', { params: { page: 1, limit: 500 } }),
    http.get('/manufacturing-partners', { params: { page: 1, limit: 500 } }),
  ])
  companyOptions.value = co.data.items
  productOptions.value = pr.data.items
  partnerOptions.value = pa.data.items
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, limit: limit.value }
    if (filters.sample_status) params.sample_status = filters.sample_status
    if (filters.company_id) params.company_id = filters.company_id
    if (filters.product_id) params.product_id = filters.product_id
    if (filters.manufacturing_partner_id) params.manufacturing_partner_id = filters.manufacturing_partner_id
    if (filters.delivered_no_feedback) params.delivered_no_feedback = true
    if (filters.follow_up_due) params.follow_up_due = true
    if (filters.converted_to_order !== undefined) params.converted_to_order = filters.converted_to_order
    const { data } = await http.get('/samples', { params })
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
