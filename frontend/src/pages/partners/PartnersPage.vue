<template>
  <div>
    <h2 class="mb-4 text-xl font-semibold text-slate-800">Manufacturing partners</h2>
    <el-table :data="rows" stripe v-loading="loading">
      <el-table-column label="Name" min-width="180">
        <template #default="{ row }">
          <router-link class="text-blue-600 hover:underline" :to="{ name: 'partner-detail', params: { partnerId: row.id } }">
            {{ row.partner_name }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="partner_type" label="Type" width="200" />
      <el-table-column prop="country" label="Country" width="100" />
      <el-table-column prop="risk_level" label="Risk" width="90" />
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
    const { data } = await http.get('/manufacturing-partners', { params: { page: page.value, limit: limit.value } })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
