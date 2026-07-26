<template>
  <div class="space-y-6">
    <section>
      <h2 class="mb-2 text-xl font-semibold text-slate-800">平台能力矩阵</h2>
      <el-table :data="benchmarks" stripe v-loading="loading">
        <el-table-column prop="platform_name" label="平台" width="140" />
        <el-table-column prop="capability_area" label="能力域" width="160" />
        <el-table-column prop="capability_description" label="描述" min-width="200" />
        <el-table-column label="PartnerOS" width="90">
          <template #default="{ row }">{{ row.partneros_has ? '有' : '无' }}</template>
        </el-table-column>
        <el-table-column prop="build_priority" label="优先级" width="80" />
        <el-table-column prop="partneros_gap_notes" label="差距" min-width="180" show-overflow-tooltip />
      </el-table>
    </section>
    <section>
      <h3 class="mb-2 font-semibold text-slate-800">渠道情报（人工/导入）</h3>
      <el-table :data="channels" stripe size="small">
        <el-table-column prop="channel_source" label="渠道" width="120" />
        <el-table-column prop="period_label" label="周期" width="100" />
        <el-table-column prop="lead_count" label="线索" width="80" />
        <el-table-column prop="quote_count" label="报价" width="80" />
        <el-table-column prop="win_count" label="赢单" width="80" />
        <el-table-column prop="quote_rate" label="报价率" width="90" />
        <el-table-column prop="win_rate" label="赢单率" width="90" />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '@/api/http'

const benchmarks = ref<unknown[]>([])
const channels = ref<unknown[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const [b, c] = await Promise.all([
      http.get('/platform-intelligence/benchmarks', { params: { limit: 50 } }),
      http.get('/platform-intelligence/channels', { params: { limit: 20 } }),
    ])
    benchmarks.value = b.data.items
    channels.value = c.data.items
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
