<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="text-base font-semibold text-slate-800">产品机会摘要</h3>
          <p class="text-xs text-slate-500">批量查看产品匹配度与报价准备度。</p>
        </div>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-4" :title="PRODUCT_OPPORTUNITY_SAFETY" />

    <el-alert
      v-if="error"
      type="error"
      :closable="false"
      show-icon
      class="mb-4"
      title="产品机会摘要暂不可用"
      :description="error"
    />

    <el-alert
      v-else-if="data?.degraded"
      type="warning"
      :closable="false"
      show-icon
      class="mb-4"
      title="降级模式"
      :description="data.warnings?.[0] || '看板数据暂不可用。'"
    />

    <div v-if="data && !error" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <SummaryCard
        v-for="card in DASHBOARD_OPPORTUNITY_CARDS"
        :key="card.key"
        :label="card.label"
        :value="data.summary[card.summaryKey]"
        :tone="card.tone"
        :to="productFilterQueryPath(card.key)"
      />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchProductOpportunityBoard, type ProductOpportunityBoardResponse } from '@/api/productOpportunity'
import { formatApiError } from '@/api/errors'
import {
  DASHBOARD_OPPORTUNITY_CARDS,
  PRODUCT_OPPORTUNITY_SAFETY,
  productFilterQueryPath,
} from '@/constants/productOpportunity'
import SummaryCard from './SummaryCard.vue'

const loading = ref(false)
const error = ref<string | null>(null)
const data = ref<ProductOpportunityBoardResponse | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    data.value = await fetchProductOpportunityBoard()
  } catch (e) {
    error.value = formatApiError(e, '请检查 VITE_API_PROXY_TARGET 和 backend 状态。')
    data.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)

defineExpose({ load, data, error, loading, PRODUCT_OPPORTUNITY_SAFETY })
</script>
