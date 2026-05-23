<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchProductAwareDraft, type ProductAwareDraftRequest } from '@/api/productAwareDraft'
import type { ProductAwareDraft } from '@/constants/productAwareDraft'
import { formatApiError } from '@/api/errors'
import {
  PRODUCT_AWARE_DRAFT_SAFETY,
  DRAFT_CHANNEL_OPTIONS,
  DRAFT_PURPOSE_OPTIONS,
  DRAFT_TONE_OPTIONS,
} from '@/constants/productAwareDraft'

const props = defineProps<{
  leadId: string | null
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const draft = ref<ProductAwareDraft | null>(null)

const channel = ref('email_intro')
const draftPurpose = ref('product_discovery')
const tone = ref('concise')

async function generate() {
  if (!props.leadId) return
  loading.value = true
  error.value = null
  try {
    const body: ProductAwareDraftRequest = {
      channel: channel.value,
      draft_purpose: draftPurpose.value,
      tone: tone.value,
      language: 'en',
      include_questions: true,
      include_product_brief: true,
    }
    draft.value = await fetchProductAwareDraft(props.leadId, body)
  } catch (e) {
    draft.value = null
    error.value = formatApiError(
      e,
      'Could not generate product-aware draft. Check VITE_API_PROXY_TARGET.',
    )
  } finally {
    loading.value = false
  }
}

watch(
  () => props.leadId,
  () => {
    draft.value = null
    error.value = null
  },
)

async function copyText(text: string, label: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`${label} copied.`)
  } catch {
    ElMessage.error('Copy failed.')
  }
}

function copyDraft() {
  if (!draft.value) return
  const parts: string[] = []
  if (draft.value.subject) parts.push(draft.value.subject)
  if (draft.value.body) parts.push(draft.value.body)
  if (draft.value.linkedin_note) parts.push(draft.value.linkedin_note)
  if (parts.length) copyText(parts.join('\n\n'), 'Draft')
}

function copyQuestions() {
  if (!draft.value?.questions.length) return
  copyText(draft.value.questions.join('\n\n'), 'Questions')
}

defineExpose({ generate, copyDraft, copyQuestions, PRODUCT_AWARE_DRAFT_SAFETY, draft })
</script>

<template>
  <el-card v-if="leadId" shadow="never" class="mb-4">
    <template #header>
      <h3 class="text-base font-semibold text-slate-800">Product-Aware Draft</h3>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-3" :title="PRODUCT_AWARE_DRAFT_SAFETY" />

    <div class="mb-3 flex flex-wrap gap-2">
      <el-select v-model="channel" size="small" class="w-40">
        <el-option v-for="o in DRAFT_CHANNEL_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-select v-model="draftPurpose" size="small" class="w-44">
        <el-option v-for="o in DRAFT_PURPOSE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-select v-model="tone" size="small" class="w-28">
        <el-option v-for="o in DRAFT_TONE_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-button size="small" type="primary" :loading="loading" @click="generate">
        Generate Product-Aware Draft
      </el-button>
    </div>

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />

    <template v-if="draft && !error">
      <p v-if="draft.subject" class="mb-1 text-xs font-medium text-slate-600">Subject</p>
      <el-input v-if="draft.subject" readonly :model-value="draft.subject" class="mb-3" />

      <p v-if="draft.body" class="mb-1 text-xs font-medium text-slate-600">Body</p>
      <el-input v-if="draft.body" type="textarea" :rows="8" readonly :model-value="draft.body" class="mb-3" />

      <p v-if="draft.linkedin_note" class="mb-1 text-xs font-medium text-slate-600">
        LinkedIn note ({{ draft.linkedin_note.length }} chars)
      </p>
      <el-input
        v-if="draft.linkedin_note"
        type="textarea"
        :rows="3"
        readonly
        :model-value="draft.linkedin_note"
        class="mb-3"
      />

      <div v-if="draft.questions.length" class="mb-3">
        <p class="mb-1 text-xs font-medium text-slate-600">Discovery questions</p>
        <ol class="list-decimal space-y-1 pl-5 text-xs text-slate-700">
          <li v-for="(q, i) in draft.questions" :key="i">{{ q }}</li>
        </ol>
      </div>

      <p class="mb-2 text-sm text-slate-700">
        <span class="font-medium">Recommended next action:</span> {{ draft.recommended_next_action }}
      </p>
      <p class="mb-3 text-xs text-slate-500">
        Suggested follow-up: {{ draft.suggested_follow_up_days }} days after manual send.
      </p>

      <div class="flex flex-wrap gap-2">
        <el-button size="small" @click="copyDraft">Copy Draft</el-button>
        <el-button size="small" @click="copyQuestions">Copy Questions</el-button>
      </div>
    </template>
  </el-card>
</template>
