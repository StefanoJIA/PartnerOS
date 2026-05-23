<template>
  <div>
    <h2 class="mb-4 text-xl font-semibold text-slate-800">AI outputs</h2>
    <el-table :data="rows" stripe>
      <el-table-column prop="task_type" label="Task" width="180" />
      <el-table-column prop="status" label="Status" width="100" />
      <el-table-column prop="model" label="Model" width="140" />
      <el-table-column label="Preview">
        <template #default="{ row }">
          <span class="line-clamp-2 text-sm text-slate-600">{{ row.output_text }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '@/api/http'

const rows = ref<unknown[]>([])

onMounted(async () => {
  const { data } = await http.get('/ai/outputs', { params: { limit: 50 } })
  rows.value = data.items
})
</script>
