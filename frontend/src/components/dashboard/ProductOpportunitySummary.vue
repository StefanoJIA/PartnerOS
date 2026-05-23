<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="text-base font-semibold text-slate-800">Product Opportunity Summary</h3>
          <p class="text-xs text-slate-500">Batch product fit and quote-readiness overview (D5.13)</p>
        </div>
        <el-button size="small" @click="load">Refresh</el-button>
      </div>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-4" :title="PRODUCT_OPPORTUNITY_SAFETY" />

    <el-alert
      v-if="error"
      type="error"
      :closable="false"
      show-icon
      class="mb-4"
      title="Product opportunity summary unavailable"
      :description="error"
    />

    <el-alert
      v-else-if="data?.degraded"
      type="warning"
      :closable="false"
      show-icon
      class="mb-4"
      title="Degraded mode"
      :description="data.warnings?.[0] || 'Board data unavailable.'"
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
    error.value = formatApiError(e, 'Check VITE_API_PROXY_TARGET and backend status.')
    data.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)

defineExpose({ load, data, error, loading, PRODUCT_OPPORTUNITY_SAFETY })
</script>
