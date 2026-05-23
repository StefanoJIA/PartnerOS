<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchPreQuoteBrief, type PreQuoteBrief } from '@/api/preQuotePrep'
import { formatApiError } from '@/api/errors'
import {
  PRE_QUOTE_PREP_SAFETY,
  PRODUCT_FOCUS_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  quoteReadinessTagType,
} from '@/constants/preQuotePrep'

const props = defineProps<{
  leadId: string | null
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const brief = ref<PreQuoteBrief | null>(null)

async function load() {
  if (!props.leadId) {
    brief.value = null
    error.value = null
    return
  }
  loading.value = true
  error.value = null
  try {
    brief.value = await fetchPreQuoteBrief(props.leadId)
  } catch (e) {
    brief.value = null
    error.value = formatApiError(
      e,
      'Could not load pre-quote brief. Check VITE_API_PROXY_TARGET points to the running backend.',
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

function copyPreQuoteBrief() {
  if (brief.value?.pre_quote_brief_text) copyText(brief.value.pre_quote_brief_text, 'Pre-quote brief')
}

function copySampleBrief() {
  if (brief.value?.sample_discussion_brief_text) {
    copyText(brief.value.sample_discussion_brief_text, 'Sample discussion brief')
  }
}

function copyQuestions() {
  if (!brief.value?.recommended_customer_questions.length) return
  copyText(brief.value.recommended_customer_questions.join('\n\n'), 'Customer questions')
}

defineExpose({ brief, load, PRE_QUOTE_PREP_SAFETY, copyPreQuoteBrief, copyQuestions })
</script>

<template>
  <el-card v-if="leadId" v-loading="loading" shadow="never" class="mb-4">
    <template #header>
      <h3 class="text-base font-semibold text-slate-800">Pre-Quote &amp; Sample Prep</h3>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-3" :title="PRE_QUOTE_PREP_SAFETY" />

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />

    <template v-if="brief && !error">
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <el-tag size="small" :type="quoteReadinessTagType(brief.quote_readiness)" effect="plain">
          Quote: {{ QUOTE_READINESS_LABELS[brief.quote_readiness] || brief.quote_readiness }}
        </el-tag>
        <el-tag size="small" type="info" effect="plain">
          Sample: {{ SAMPLE_READINESS_LABELS[brief.sample_readiness] || brief.sample_readiness }}
        </el-tag>
        <span class="text-sm text-slate-600">Score: {{ brief.opportunity_score }}/100</span>
      </div>

      <div v-if="brief.recommended_product_focus.length" class="mb-3 flex flex-wrap gap-1">
        <el-tag
          v-for="f in brief.recommended_product_focus"
          :key="f"
          size="small"
          type="primary"
          effect="plain"
        >
          {{ PRODUCT_FOCUS_LABELS[f] || f }}
        </el-tag>
      </div>

      <div v-if="brief.missing_quote_info.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Missing quote info</p>
        <ul class="list-inside list-disc text-xs text-amber-800">
          <li v-for="item in brief.missing_quote_info" :key="item">
            {{ MISSING_QUOTE_INFO_LABELS[item] || item }}
          </li>
        </ul>
      </div>

      <div class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Quote preparation checklist</p>
        <ul class="list-inside list-disc text-xs text-slate-700">
          <li v-for="(item, i) in brief.quote_preparation_checklist.slice(0, 8)" :key="i">{{ item }}</li>
        </ul>
      </div>

      <div class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Sample preparation checklist</p>
        <ul class="list-inside list-disc text-xs text-slate-700">
          <li v-for="(item, i) in brief.sample_preparation_checklist.slice(0, 6)" :key="i">{{ item }}</li>
        </ul>
      </div>

      <div v-if="brief.recommended_customer_questions.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Recommended customer questions</p>
        <ol class="list-decimal space-y-1 pl-5 text-xs text-slate-700">
          <li v-for="(q, i) in brief.recommended_customer_questions" :key="i">{{ q }}</li>
        </ol>
      </div>

      <div v-if="brief.recommended_internal_next_steps.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Internal next steps</p>
        <ul class="list-inside list-disc text-xs text-slate-600">
          <li v-for="(s, i) in brief.recommended_internal_next_steps" :key="i">{{ s }}</li>
        </ul>
      </div>

      <p class="mb-3 text-sm text-slate-700">
        <span class="font-medium">Next action:</span> {{ brief.recommended_next_action }}
      </p>

      <div class="flex flex-wrap gap-2">
        <el-button size="small" @click="copyPreQuoteBrief">Copy Pre-Quote Brief</el-button>
        <el-button size="small" @click="copySampleBrief">Copy Sample Discussion Brief</el-button>
        <el-button size="small" @click="copyQuestions">Copy Customer Questions</el-button>
      </div>
    </template>
  </el-card>
</template>
