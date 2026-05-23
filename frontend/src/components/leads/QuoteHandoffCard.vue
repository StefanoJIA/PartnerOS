<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchQuoteHandoffBrief, type QuoteHandoffBrief } from '@/api/quoteHandoff'
import { formatApiError } from '@/api/errors'
import {
  QUOTE_HANDOFF_SAFETY,
  HANDOFF_STATUS_LABELS,
  HANDOFF_PRIORITY_LABELS,
  PARTNER_ROUTE_LABELS,
  PRODUCT_SCOPE_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  handoffStatusTagType,
  handoffPriorityTagType,
  quoteReadinessTagType,
} from '@/constants/quoteHandoff'

const props = defineProps<{
  leadId: string | null
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const brief = ref<QuoteHandoffBrief | null>(null)

async function load() {
  if (!props.leadId) {
    brief.value = null
    error.value = null
    return
  }
  loading.value = true
  error.value = null
  try {
    brief.value = await fetchQuoteHandoffBrief(props.leadId)
  } catch (e) {
    brief.value = null
    error.value = formatApiError(
      e,
      'Could not load quote handoff brief. Check VITE_API_PROXY_TARGET points to the running backend.',
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

function copyHandoffBrief() {
  if (brief.value?.quote_handoff_brief_text) {
    copyText(brief.value.quote_handoff_brief_text, 'Quote handoff brief')
  }
}

function copySupplierNotes() {
  if (brief.value?.supplier_notes_text) {
    copyText(brief.value.supplier_notes_text, 'Supplier notes')
  }
}

function copyCustomerQuestions() {
  if (brief.value?.customer_questions_text) {
    copyText(brief.value.customer_questions_text, 'Customer questions')
  }
}

defineExpose({
  brief,
  load,
  QUOTE_HANDOFF_SAFETY,
  copyHandoffBrief,
  copySupplierNotes,
  copyCustomerQuestions,
})
</script>

<template>
  <el-card v-if="leadId" v-loading="loading" shadow="never" class="mb-4">
    <template #header>
      <h3 class="text-base font-semibold text-slate-800">Soft Quote Handoff</h3>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-3" :title="QUOTE_HANDOFF_SAFETY" />

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />

    <p v-if="!brief && !error && !loading" class="text-sm text-slate-500">
      Select a lead to view quote handoff preparation.
    </p>

    <template v-if="brief && !error">
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <el-tag size="small" :type="handoffStatusTagType(brief.handoff_status)" effect="plain">
          {{ HANDOFF_STATUS_LABELS[brief.handoff_status] || brief.handoff_status }}
        </el-tag>
        <el-tag size="small" :type="handoffPriorityTagType(brief.handoff_priority)" effect="plain">
          Priority: {{ HANDOFF_PRIORITY_LABELS[brief.handoff_priority] || brief.handoff_priority }}
        </el-tag>
        <el-tag size="small" :type="quoteReadinessTagType(brief.quote_readiness)" effect="plain">
          Quote: {{ QUOTE_READINESS_LABELS[brief.quote_readiness] || brief.quote_readiness }}
        </el-tag>
        <el-tag size="small" type="info" effect="plain">
          Sample: {{ SAMPLE_READINESS_LABELS[brief.sample_readiness] || brief.sample_readiness }}
        </el-tag>
      </div>

      <div v-if="brief.recommended_partner_route.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Recommended partner route</p>
        <div class="flex flex-wrap gap-1">
          <el-tag
            v-for="r in brief.recommended_partner_route"
            :key="r"
            size="small"
            type="primary"
            effect="plain"
          >
            {{ PARTNER_ROUTE_LABELS[r] || r }}
          </el-tag>
        </div>
      </div>

      <div v-if="brief.recommended_product_scope.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Product scope</p>
        <div class="flex flex-wrap gap-1">
          <el-tag
            v-for="s in brief.recommended_product_scope"
            :key="s"
            size="small"
            type="success"
            effect="plain"
          >
            {{ PRODUCT_SCOPE_LABELS[s] || s }}
          </el-tag>
        </div>
      </div>

      <div v-if="brief.known_context.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Known context</p>
        <ul class="list-inside list-disc text-xs text-slate-700">
          <li v-for="(ctx, i) in brief.known_context" :key="i">{{ ctx }}</li>
        </ul>
      </div>

      <div v-if="brief.missing_customer_info.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Missing customer info</p>
        <ul class="list-inside list-disc text-xs text-amber-800">
          <li v-for="item in brief.missing_customer_info" :key="item">
            {{ MISSING_QUOTE_INFO_LABELS[item] || item.replace(/_/g, ' ') }}
          </li>
        </ul>
      </div>

      <div v-if="brief.customer_clarification_questions.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Customer clarification questions</p>
        <ol class="list-decimal space-y-1 pl-5 text-xs text-slate-700">
          <li v-for="(q, i) in brief.customer_clarification_questions" :key="i">{{ q }}</li>
        </ol>
      </div>

      <div v-if="brief.supplier_preparation_notes.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Supplier preparation notes (internal)</p>
        <ul class="list-inside list-disc text-xs text-slate-600">
          <li v-for="(n, i) in brief.supplier_preparation_notes" :key="i">{{ n }}</li>
        </ul>
      </div>

      <p class="mb-3 text-sm text-slate-700">
        <span class="font-medium">Recommended next step:</span> {{ brief.recommended_next_step }}
      </p>

      <div class="flex flex-wrap gap-2">
        <el-button size="small" type="primary" @click="copyHandoffBrief">Copy Quote Handoff Brief</el-button>
        <el-button size="small" @click="copySupplierNotes">Copy Supplier Notes</el-button>
        <el-button size="small" @click="copyCustomerQuestions">Copy Customer Questions</el-button>
      </div>
    </template>
  </el-card>
</template>
