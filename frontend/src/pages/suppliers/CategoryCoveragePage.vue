<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="mb-1 text-xl font-semibold text-slate-800">品类覆盖工作台</h2>
        <p class="text-sm text-slate-500">三大行业客户需求 vs 活跃/候选供应商覆盖 — 无自动激活。</p>
      </div>
      <el-button type="primary" :loading="refreshing" @click="refreshAll">刷新覆盖评估</el-button>
    </div>

    <el-row :gutter="16">
      <el-col v-for="row in rows" :key="row.industry_vertical" :span="8" class="mb-4">
        <el-card shadow="hover">
          <template #header>
            <span class="font-medium">{{ industryLabel(row.industry_vertical) }}</span>
          </template>
          <p class="mb-2 text-sm text-slate-600">活跃 Partner：{{ row.coverage_json?.active_partner_count ?? 0 }}</p>
          <p class="mb-2 text-sm text-slate-600">公开候选：{{ row.coverage_json?.public_candidate_count ?? 0 }}</p>
          <p class="mb-2 text-sm text-amber-700" v-if="row.risk_json?.single_supplier_dependency">单供应商依赖风险</p>
          <el-tag v-for="gap in (row.gaps_json?.gaps || []).slice(0, 4)" :key="gap.need" class="mr-1 mb-1" type="warning">
            {{ gap.need }}
          </el-tag>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '@/api/http'

const INDUSTRY_LABELS: Record<string, string> = {
  lifting_systems: 'A · 升降桌架/立柱',
  education_furniture: 'B · 教育家具',
  contract_office: 'C · 合同办公家具',
}

interface CoverageRow {
  industry_vertical: string
  coverage_json?: { active_partner_count?: number; public_candidate_count?: number }
  gaps_json?: { gaps?: { need: string }[] }
  risk_json?: { single_supplier_dependency?: boolean }
}

const rows = ref<CoverageRow[]>([])
const refreshing = ref(false)

function industryLabel(v: string) {
  return INDUSTRY_LABELS[v] || v
}

async function load() {
  const { data } = await http.get('/commercial-pilot/category-coverage')
  rows.value = data
}

async function refreshAll() {
  refreshing.value = true
  try {
    for (const key of Object.keys(INDUSTRY_LABELS)) {
      await http.post(`/commercial-pilot/category-coverage/${key}/refresh`)
    }
    await load()
    ElMessage.success('覆盖评估已刷新')
  } finally {
    refreshing.value = false
  }
}

onMounted(load)
</script>
