<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="mb-1 text-xl font-semibold text-slate-800">Commercial Pilot 运营</h2>
        <p class="text-sm text-slate-500">合成客户试点 — 候选匹配、QIC、区间报价/PDF、MR 草稿；场景价禁止外发。</p>
      </div>
    </div>

    <el-card class="mb-4" shadow="never">
      <template #header>商业指标</template>
      <el-descriptions v-if="metrics" :column="3" border size="small">
        <el-descriptions-item label="公开候选">{{ metrics.candidate_suppliers }}</el-descriptions-item>
        <el-descriptions-item label="资质转化">{{ metrics.qualification_conversion_pct }}%</el-descriptions-item>
        <el-descriptions-item label="开放开发任务">{{ metrics.open_development_tasks }}</el-descriptions-item>
        <el-descriptions-item label="2+候选项目">{{ metrics.projects_with_2_plus_candidates }}</el-descriptions-item>
        <el-descriptions-item label="试点含报价">{{ metrics.pilots_with_quotes }}</el-descriptions-item>
        <el-descriptions-item label="场景价封锁">{{ metrics.quote_readiness_blocked_scenario ? '是' : '否' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-table :data="pilots" stripe v-loading="loading">
      <el-table-column prop="pilot_code" label="代码" width="160" />
      <el-table-column prop="pilot_name" label="名称" min-width="220" />
      <el-table-column label="行业" width="140">
        <template #default="{ row }">{{ industryLabel(row.industry_vertical) }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="候选" width="80">
        <template #default="{ row }">{{ row.candidate_summary_json?.count ?? '—' }}</template>
      </el-table-column>
      <el-table-column prop="result_summary" label="结果摘要" min-width="260" show-overflow-tooltip />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '@/api/http'

const INDUSTRY_LABELS: Record<string, string> = {
  lifting_systems: '升降系统',
  education_furniture: '教育家具',
  contract_office: '合同办公',
}

interface Metrics {
  candidate_suppliers: number
  qualification_conversion_pct: number
  open_development_tasks: number
  projects_with_2_plus_candidates: number
  pilots_with_quotes: number
  quote_readiness_blocked_scenario: boolean
}

interface PilotRow {
  pilot_code: string
  pilot_name: string
  industry_vertical: string
  status: string
  candidate_summary_json?: { count?: number }
  result_summary?: string
}

const metrics = ref<Metrics | null>(null)
const pilots = ref<PilotRow[]>([])
const loading = ref(false)

function industryLabel(v: string) {
  return INDUSTRY_LABELS[v] || v
}

async function load() {
  loading.value = true
  try {
    const [m, p] = await Promise.all([
      http.get('/commercial-pilot/metrics'),
      http.get('/commercial-pilot/pilots'),
    ])
    metrics.value = m.data
    pilots.value = p.data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
