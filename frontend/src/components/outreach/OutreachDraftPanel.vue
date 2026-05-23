<template>
  <el-card v-if="companyId" shadow="never" class="mb-4">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <span class="font-medium text-slate-800">Outreach Draft (copy only)</span>
        <el-button size="small" type="primary" :loading="loading" @click="generate">Generate Draft</el-button>
      </div>
    </template>

    <p class="mb-3 text-xs text-slate-500">
      Human-reviewed drafts only — not sent. Copy to LinkedIn or Outlook manually, then log a touchpoint below.
    </p>

    <div class="mb-3 flex flex-wrap gap-2">
      <el-select v-model="channel" size="small" class="w-40">
        <el-option label="LinkedIn connect" value="linkedin_connect" />
        <el-option label="LinkedIn follow-up" value="linkedin_followup" />
        <el-option label="Email intro" value="email_intro" />
        <el-option label="Email follow-up" value="email_followup" />
      </el-select>
      <el-select v-model="productFocus" size="small" class="w-44">
        <el-option label="Lifting Systems" value="hosun_lifting" />
        <el-option label="Education Furniture" value="jooboo_education" />
        <el-option label="Medical Workspace" value="medical_workspace" />
        <el-option label="General" value="general" />
      </el-select>
    </div>

    <el-alert v-if="error" type="error" :closable="false" class="mb-3" :title="error" />

    <template v-if="draft">
      <div v-if="draft.linkedin_connect_note" class="mb-3">
        <p class="text-xs font-medium text-slate-600">LinkedIn note</p>
        <el-input type="textarea" :rows="3" readonly :model-value="draft.linkedin_connect_note" />
        <el-button size="small" class="mt-1" @click="copy(draft.linkedin_connect_note!)">Copy</el-button>
      </div>
      <div v-if="draft.email_subject" class="mb-3">
        <p class="text-xs font-medium text-slate-600">Email subject</p>
        <el-input readonly :model-value="draft.email_subject" />
        <el-button size="small" class="mt-1" @click="copy(draft.email_subject!)">Copy subject</el-button>
      </div>
      <div v-if="draft.email_body" class="mb-3">
        <p class="text-xs font-medium text-slate-600">Email body</p>
        <el-input type="textarea" :rows="6" readonly :model-value="draft.email_body" />
        <el-button size="small" class="mt-1" @click="copy(draft.email_body!)">Copy body</el-button>
      </div>
      <p class="text-xs text-slate-600">
        <span class="font-medium">Suggested next action:</span> {{ draft.suggested_next_action }}
        <el-button size="small" link type="primary" @click="emit('use-next-action', draft.suggested_next_action)">
          Use in form
        </el-button>
      </p>
      <p class="text-xs text-slate-400">Touchpoint type hint: {{ draft.suggested_touchpoint_type }}</p>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchOutreachDraft, type OutreachDraft } from '@/api/outreachDraft'

const props = defineProps<{ companyId: string | null }>()
const emit = defineEmits<{ (e: 'use-next-action', value: string): void }>()

const loading = ref(false)
const error = ref('')
const draft = ref<OutreachDraft | null>(null)
const channel = ref('linkedin_connect')
const productFocus = ref('general')

watch(
  () => props.companyId,
  () => {
    draft.value = null
    error.value = ''
  },
)

async function generate() {
  if (!props.companyId) return
  loading.value = true
  error.value = ''
  try {
    draft.value = await fetchOutreachDraft({
      companyId: props.companyId,
      channel: channel.value,
      productFocus: productFocus.value,
    })
  } catch (e: unknown) {
    error.value = 'Failed to generate draft'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function copy(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('Copied to clipboard')
  } catch {
    ElMessage.warning('Copy failed — select text manually')
  }
}
</script>
