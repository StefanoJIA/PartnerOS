<template>
  <div>
    <h2 class="mb-2 text-xl font-semibold text-slate-800">行业 Benchmark 知识库</h2>
    <p class="mb-4 text-sm text-amber-700">行业参考 — 非 partner、非授权经销商。不可用于正式报价。</p>
    <el-table :data="rows" stripe v-loading="loading">
      <el-table-column prop="display_name" label="品牌" min-width="200" />
      <el-table-column prop="industry_vertical" label="垂直" width="160" />
      <el-table-column prop="country" label="国家" width="100" />
      <el-table-column prop="review_status" label="审核" width="100" />
      <el-table-column prop="relationship_disclaimer" label="免责声明" min-width="240" show-overflow-tooltip />
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
    const { data } = await http.get('/benchmark-brands', { params: { page: page.value, limit: limit.value } })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
