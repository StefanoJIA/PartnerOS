<template>
  <div>
    <h2 class="mb-2 text-xl font-semibold text-slate-800">供应商发现与资质</h2>
    <p class="mb-4 text-sm text-slate-500">人工录入与评估 — 无自动联系、承诺或激活。</p>
    <el-table :data="rows" stripe v-loading="loading">
      <el-table-column prop="company_name" label="公司" min-width="180" />
      <el-table-column prop="brand_name" label="品牌" width="140" />
      <el-table-column prop="country" label="国家" width="100" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column prop="risk_level" label="风险" width="90" />
      <el-table-column prop="doc_completeness_pct" label="资料完整度" width="110" />
      <el-table-column prop="data_source" label="来源" width="100" />
    </el-table>
    <el-pagination class="mt-4" background layout="prev, pager, next" :total="total" v-model:current-page="page" :page-size="limit" @current-change="load" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '@/api/http'

const rows = ref<unknown[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await http.get('/supplier-discovery', { params: { page: page.value, limit: limit.value } })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
