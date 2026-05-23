<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchProductOpportunityBoard } from '@/api/productOpportunity'
import { formatApiError } from '@/api/errors'
import {
  COMMON_QUOTE_QUESTIONS,
  MISSING_QUOTE_INFO_LABELS,
  OPPORTUNITY_LEVEL_LABELS,
  PRODUCT_FOCUS_LABELS,
  PRODUCT_OPPORTUNITY_FILTER_OPTIONS,
  PRODUCT_OPPORTUNITY_SAFETY,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  filterProductOpportunityRows,
  mapBoardRow,
  quoteReadinessAdvice,
  opportunityLevelTagType,
  quoteReadinessTagType,
  type ProductOpportunityFilterKey,
  type ProductOpportunityBoardRow,
} from '@/constants/productOpportunity'

const props = defineProps<{
  externalFilter?: ProductOpportunityFilterKey | null
}>()

const emit = defineEmits<{
  selectLead: [leadId: string]
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const filter = ref<ProductOpportunityFilterKey>('all')
const allRows = ref<ProductOpportunityBoardRow[]>([])
const missingInfoSummary = ref<Record<string, number>>({})
const degraded = ref(false)

const filteredRows = computed(() => filterProductOpportunityRows(allRows.value, filter.value))

const topMissingInfo = computed(() =>
  Object.entries(missingInfoSummary.value)
    .slice(0, 7)
    .map(([key, count]) => ({ key, count, label: MISSING_QUOTE_INFO_LABELS[key] || key })),
)

watch(
  () => props.externalFilter,
  (v) => {
    if (v) filter.value = v
  },
  { immediate: true },
)

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await fetchProductOpportunityBoard()
    allRows.value = data.rows.map(mapBoardRow)
    missingInfoSummary.value = data.missing_info_summary || {}
    degraded.value = data.degraded
  } catch (e) {
    allRows.value = []
    missingInfoSummary.value = {}
    error.value = formatApiError(
      e,
      'Could not load product opportunity board. Check VITE_API_PROXY_TARGET.',
    )
  } finally {
    loading.value = false
  }
}

function onRowClick(row: ProductOpportunityBoardRow) {
  emit('selectLead', row.leadId)
}

async function copyCommonQuestions() {
  try {
    await navigator.clipboard.writeText(COMMON_QUOTE_QUESTIONS)
    ElMessage.success('Common questions copied.')
  } catch {
    ElMessage.error('Copy failed.')
  }
}

function missingInfoLabel(key: string) {
  return MISSING_QUOTE_INFO_LABELS[key] || key
}

onMounted(load)

defineExpose({
  load,
  filter,
  filteredRows,
  copyCommonQuestions,
  PRODUCT_OPPORTUNITY_SAFETY,
  COMMON_QUOTE_QUESTIONS,
})
</script>

<template>
  <el-card v-loading="loading" shadow="never">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 class="text-lg font-semibold text-slate-800">Product Opportunity Board</h2>
          <p class="mt-1 text-xs text-slate-500">
            Batch quote-readiness and product focus — advisory only (D5.13)
          </p>
        </div>
        <el-button size="small" @click="load">Refresh</el-button>
      </div>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-3" :title="PRODUCT_OPPORTUNITY_SAFETY" />

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />

    <el-alert
      v-else-if="degraded"
      type="warning"
      :closable="false"
      show-icon
      class="mb-3"
      title="Degraded mode — board may be empty."
    />

    <div v-if="topMissingInfo.length" class="mb-3 rounded border border-amber-100 bg-amber-50 p-3">
      <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p class="text-sm font-medium text-amber-900">Most Common Missing Quote Info</p>
        <el-button size="small" @click="copyCommonQuestions">Copy Common Questions</el-button>
      </div>
      <ul class="grid gap-1 text-xs text-amber-800 sm:grid-cols-2">
        <li v-for="item in topMissingInfo" :key="item.key">
          {{ item.label }}: {{ item.count }}
        </li>
      </ul>
    </div>

    <p class="mb-1 text-xs font-medium text-slate-600">Product opportunity filters</p>
    <el-radio-group v-model="filter" size="small" class="mb-3 flex flex-wrap gap-1">
      <el-radio-button v-for="opt in PRODUCT_OPPORTUNITY_FILTER_OPTIONS" :key="opt.key" :value="opt.key">
        {{ opt.label }}
      </el-radio-button>
    </el-radio-group>

    <el-table
      :data="filteredRows"
      size="small"
      stripe
      highlight-current-row
      empty-text="No leads match this filter."
      @row-click="onRowClick"
    >
      <el-table-column prop="companyName" label="Company" min-width="130" show-overflow-tooltip />
      <el-table-column label="Score" width="64" sortable prop="opportunityScore" />
      <el-table-column label="Level" width="130">
        <template #default="{ row }">
          <el-tag size="small" :type="opportunityLevelTagType(row.opportunityLevel)" effect="plain">
            {{ OPPORTUNITY_LEVEL_LABELS[row.opportunityLevel] || row.opportunityLevel }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Product Focus" min-width="160">
        <template #default="{ row }">
          <div class="flex flex-wrap gap-1">
            <el-tag
              v-for="f in row.productFocus.slice(0, 2)"
              :key="f"
              size="small"
              type="primary"
              effect="plain"
            >
              {{ PRODUCT_FOCUS_LABELS[f] || f }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="Quote" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="quoteReadinessTagType(row.quoteReadiness)" effect="plain">
            {{ QUOTE_READINESS_LABELS[row.quoteReadiness] || row.quoteReadiness }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Sample" width="100">
        <template #default="{ row }">
          <span class="text-xs">{{ SAMPLE_READINESS_LABELS[row.sampleReadiness] || row.sampleReadiness }}</span>
        </template>
      </el-table-column>
      <el-table-column label="Missing Info" min-width="140">
        <template #default="{ row }">
          <span v-if="row.missingQuoteInfo.length" class="text-xs text-amber-700">
            {{ row.missingQuoteInfo.slice(0, 3).map(missingInfoLabel).join(', ') }}
          </span>
          <span v-else class="text-xs text-slate-400">—</span>
        </template>
      </el-table-column>
      <el-table-column
        prop="nextProductAction"
        label="Next Product Action"
        min-width="160"
        show-overflow-tooltip
      />
      <el-table-column label="Due" width="100">
        <template #default="{ row }">
          <span class="text-xs">{{ row.dueStatus || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="" width="90" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click.stop="onRowClick(row)">Open Lead</el-button>
        </template>
      </el-table-column>
    </el-table>

    <p v-if="filteredRows.length" class="mt-2 text-xs text-slate-500">
      {{ quoteReadinessAdvice(filteredRows[0].quoteReadiness, filteredRows[0].sampleReadiness) }}
    </p>
  </el-card>
</template>
