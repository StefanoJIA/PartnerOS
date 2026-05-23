<template>
  <div>
    <h2 class="mb-4 text-xl font-semibold text-slate-800">Market intelligence</h2>
    <p v-if="filterCompanyId" class="mb-2 text-sm text-slate-600">
      当前按公司筛选（D5）：
      <code class="rounded bg-slate-100 px-1">{{ filterCompanyId }}</code>
    </p>
    <el-table :data="rows" stripe>
      <el-table-column prop="title" label="Title" />
      <el-table-column prop="source_type" label="Source" width="120" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { http } from '@/api/http'

const route = useRoute()
const rows = ref<unknown[]>([])
const filterCompanyId = ref<string | null>(null)

async function load() {
  const companyId = typeof route.query.companyId === 'string' ? route.query.companyId : null
  filterCompanyId.value = companyId
  const params = companyId ? { related_company_id: companyId } : {}
  const { data } = await http.get('/market-intelligence', { params })
  rows.value = data.items
}

onMounted(load)
watch(() => route.query.companyId, load)
</script>
