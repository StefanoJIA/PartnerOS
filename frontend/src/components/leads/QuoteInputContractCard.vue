<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchQuoteInputContract, type QuoteInputContract } from '@/api/quoteInputContract'
import { formatApiError } from '@/api/errors'
import {
  QUOTE_INPUT_CONTRACT_SAFETY,
  QUOTE_MODULE_READINESS_LABELS,
  HANDOFF_STATUS_LABELS,
  PARTNER_ROUTE_LABELS,
  PRODUCT_SCOPE_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  KNOWN_REQUIREMENT_KEYS,
  KNOWN_REQUIREMENT_LABELS,
  quoteModuleReadinessTagType,
} from '@/constants/quoteInputContract'

const props = defineProps<{
  leadId: string | null
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const contract = ref<QuoteInputContract | null>(null)

async function load() {
  if (!props.leadId) {
    contract.value = null
    error.value = null
    return
  }
  loading.value = true
  error.value = null
  try {
    contract.value = await fetchQuoteInputContract(props.leadId)
  } catch (e) {
    contract.value = null
    error.value = formatApiError(
      e,
      'Could not load quote input contract. Check VITE_API_PROXY_TARGET points to the running backend.',
    )
  } finally {
    loading.value = false
  }
}

watch(() => props.leadId, () => load(), { immediate: true })

const knownRows = computed(() => {
  const known = contract.value?.quote_input_fields?.known_requirements
  if (!known) return []
  return KNOWN_REQUIREMENT_KEYS.map((key) => ({
    key,
    label: KNOWN_REQUIREMENT_LABELS[key] || key,
    value: known[key as keyof typeof known] || null,
  }))
})

async function copyText(text: string, label: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`${label} copied.`)
  } catch {
    ElMessage.error('Copy failed.')
  }
}

function copySummary() {
  if (contract.value?.copyable_handoff_summary) {
    copyText(contract.value.copyable_handoff_summary, 'Quote input summary')
  }
}

function copyJson() {
  if (contract.value?.copyable_json) {
    copyText(contract.value.copyable_json, 'Quote input JSON')
  }
}

function copyQuestions() {
  const qs = contract.value?.quote_input_fields?.recommended_questions || []
  if (qs.length) {
    copyText(qs.map((q, i) => `${i + 1}. ${q}`).join('\n'), 'Customer questions')
  }
}

defineExpose({
  contract,
  load,
  QUOTE_INPUT_CONTRACT_SAFETY,
  copySummary,
  copyJson,
  copyQuestions,
})
</script>

<template>
  <el-card v-if="leadId" v-loading="loading" shadow="never" class="mb-4">
    <template #header>
      <h3 class="text-base font-semibold text-slate-800">Quote Input Contract</h3>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-3" :title="QUOTE_INPUT_CONTRACT_SAFETY" />

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />

    <p v-if="!contract && !error && !loading" class="text-sm text-slate-500">
      Select a lead to view quote input contract.
    </p>

    <template v-if="contract && !error">
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <el-tag
          size="small"
          :type="quoteModuleReadinessTagType(contract.quote_module_readiness)"
          effect="plain"
        >
          {{ QUOTE_MODULE_READINESS_LABELS[contract.quote_module_readiness] || contract.quote_module_readiness }}
        </el-tag>
        <el-tag size="small" type="info" effect="plain">
          Handoff: {{ HANDOFF_STATUS_LABELS[contract.handoff_status] || contract.handoff_status }}
        </el-tag>
      </div>

      <div v-if="contract.recommended_partner_route.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Recommended route</p>
        <div class="flex flex-wrap gap-1">
          <el-tag
            v-for="r in contract.recommended_partner_route"
            :key="r"
            size="small"
            type="primary"
            effect="plain"
          >
            {{ PARTNER_ROUTE_LABELS[r] || r }}
          </el-tag>
        </div>
      </div>

      <div v-if="contract.recommended_product_scope.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Product scope</p>
        <div class="flex flex-wrap gap-1">
          <el-tag
            v-for="s in contract.recommended_product_scope"
            :key="s"
            size="small"
            type="success"
            effect="plain"
          >
            {{ PRODUCT_SCOPE_LABELS[s] || s }}
          </el-tag>
        </div>
      </div>

      <div class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Known requirements</p>
        <table class="w-full text-xs text-slate-700">
          <tbody>
            <tr v-for="row in knownRows" :key="row.key" class="border-b border-slate-100">
              <td class="py-1 pr-3 font-medium text-slate-500">{{ row.label }}</td>
              <td class="py-1">{{ row.value || 'Not confirmed' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="contract.quote_input_fields.missing_requirements.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Missing requirements</p>
        <ul class="list-inside list-disc text-xs text-amber-800">
          <li v-for="item in contract.quote_input_fields.missing_requirements" :key="item">
            {{ MISSING_QUOTE_INFO_LABELS[item] || item.replace(/_/g, ' ') }}
          </li>
        </ul>
      </div>

      <div v-if="contract.quote_input_fields.recommended_questions.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Recommended questions</p>
        <ol class="list-decimal space-y-1 pl-5 text-xs text-slate-700">
          <li v-for="(q, i) in contract.quote_input_fields.recommended_questions" :key="i">{{ q }}</li>
        </ol>
      </div>

      <div v-if="contract.quote_input_fields.supplier_preparation_notes.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Supplier preparation notes</p>
        <ul class="list-inside list-disc text-xs text-slate-600">
          <li v-for="(n, i) in contract.quote_input_fields.supplier_preparation_notes" :key="i">{{ n }}</li>
        </ul>
      </div>

      <div class="flex flex-wrap gap-2">
        <el-button size="small" type="primary" @click="copySummary">Copy Quote Input Summary</el-button>
        <el-button size="small" @click="copyJson">Copy Quote Input JSON</el-button>
        <el-button size="small" @click="copyQuestions">Copy Customer Questions</el-button>
      </div>
    </template>
  </el-card>
</template>
