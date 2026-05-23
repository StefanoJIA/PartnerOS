<template>
  <div>
    <h2 class="mb-4 text-xl font-semibold text-slate-800">Field visits</h2>
    <p class="text-sm text-slate-600">Create plans via API or extend this page. Listed plans:</p>
    <el-table class="mt-4" :data="rows" stripe>
      <el-table-column prop="plan_name" label="Plan" />
      <el-table-column prop="city" label="City" width="120" />
      <el-table-column prop="status" label="Status" width="120" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '@/api/http'

const rows = ref<unknown[]>([])

onMounted(async () => {
  const { data } = await http.get('/field-visits')
  rows.value = data.items
})
</script>
