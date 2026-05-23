<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchProductFit, type ProductFit } from '@/api/aDomain'
import { formatApiError } from '@/api/errors'
import {
  PRODUCT_FIT_SAFETY,
  PRODUCT_FOCUS_LABELS,
  OPPORTUNITY_LEVEL_LABELS,
  PROJECT_TYPE_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  opportunityLevelTagType,
  quoteReadinessTagType,
  buildProductBrief,
} from '@/constants/productFit'

const props = defineProps<{
  leadId: string | null
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const fit = ref<ProductFit | null>(null)

async function load() {
  if (!props.leadId) {
    fit.value = null
    error.value = null
    return
  }
  loading.value = true
  error.value = null
  try {
    fit.value = await fetchProductFit(props.leadId)
  } catch (e) {
    fit.value = null
    error.value = formatApiError(
      e,
      'Could not load product fit. Check that VITE_API_PROXY_TARGET points to the running backend.',
    )
  } finally {
    loading.value = false
  }
}

watch(() => props.leadId, () => load(), { immediate: true })

async function copyText(text: string, label: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`${label} copied.`)
  } catch {
    ElMessage.error('Copy failed.')
  }
}

function copyQuestions() {
  if (!fit.value?.recommended_discovery_questions.length) return
  copyText(fit.value.recommended_discovery_questions.join('\n\n'), 'Discovery questions')
}

function copyBrief() {
  if (!fit.value) return
  copyText(buildProductBrief(fit.value), 'Product brief')
}

defineExpose({ fit, load, PRODUCT_FIT_SAFETY, copyQuestions, copyBrief })
</script>

<template>
  <el-card v-if="leadId" v-loading="loading" shadow="never" class="mb-4">
    <template #header>
      <h3 class="text-base font-semibold text-slate-800">Product Fit &amp; Project Opportunity</h3>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-3" :title="PRODUCT_FIT_SAFETY" />

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />

    <template v-if="fit && !error">
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <span class="text-2xl font-bold text-slate-800">{{ fit.project_opportunity_score }}</span>
        <span class="text-sm text-slate-500">/100</span>
        <el-tag size="small" :type="opportunityLevelTagType(fit.opportunity_level)" effect="plain">
          {{ OPPORTUNITY_LEVEL_LABELS[fit.opportunity_level] || fit.opportunity_level }}
        </el-tag>
      </div>

      <dl class="mb-3 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt class="text-xs text-slate-500">Project type</dt>
          <dd class="font-medium text-slate-800">
            {{ PROJECT_TYPE_LABELS[fit.project_type] || fit.project_type }}
          </dd>
        </div>
        <div>
          <dt class="text-xs text-slate-500">Quote readiness</dt>
          <dd>
            <el-tag size="small" :type="quoteReadinessTagType(fit.quote_readiness)" effect="plain">
              {{ QUOTE_READINESS_LABELS[fit.quote_readiness] || fit.quote_readiness }}
            </el-tag>
          </dd>
        </div>
        <div>
          <dt class="text-xs text-slate-500">Sample readiness</dt>
          <dd class="font-medium text-slate-800">
            {{ SAMPLE_READINESS_LABELS[fit.sample_readiness] || fit.sample_readiness }}
          </dd>
        </div>
      </dl>

      <div v-if="fit.recommended_product_focus.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Product focus</p>
        <div class="flex flex-wrap gap-1">
          <el-tag
            v-for="focus in fit.recommended_product_focus"
            :key="focus"
            size="small"
            type="primary"
            effect="plain"
          >
            {{ PRODUCT_FOCUS_LABELS[focus] || focus }}
          </el-tag>
        </div>
      </div>

      <div v-if="fit.missing_quote_info.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Missing quote info</p>
        <ul class="list-inside list-disc text-xs text-amber-800">
          <li v-for="item in fit.missing_quote_info" :key="item">
            {{ MISSING_QUOTE_INFO_LABELS[item] || item }}
          </li>
        </ul>
      </div>

      <div v-if="fit.recommended_discovery_questions.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Discovery questions</p>
        <ol class="list-decimal space-y-1 pl-5 text-xs text-slate-700">
          <li v-for="(q, i) in fit.recommended_discovery_questions" :key="i">{{ q }}</li>
        </ol>
      </div>

      <p class="mb-2 text-sm text-slate-700">
        <span class="font-medium">Next product action:</span>
        {{ fit.recommended_next_product_action }}
      </p>
      <p class="mb-3 text-xs text-slate-600">
        <span class="font-medium">Sales angle:</span>
        {{ fit.sales_angle }}
      </p>

      <div class="flex flex-wrap gap-2">
        <el-button size="small" @click="copyQuestions">Copy Questions</el-button>
        <el-button size="small" @click="copyBrief">Copy Product Brief</el-button>
      </div>
    </template>
  </el-card>
</template>
