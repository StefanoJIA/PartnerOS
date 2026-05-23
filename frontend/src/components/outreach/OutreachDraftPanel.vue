<template>
  <el-card v-if="companyId && leadId" shadow="never" class="mb-4">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <span class="font-medium text-slate-800">Outreach Draft — Manual Send</span>
        <el-tag size="small" :type="statusTagType">{{ draftStatusLabel(draftStatus) }}</el-tag>
      </div>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-3" :title="OUTREACH_SAFETY_NOTICE" />

    <p class="mb-3 text-xs text-slate-500">
      Generate → Copy → send in LinkedIn / Outlook / Email → Mark as Sent to log touchpoint here.
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
      <el-button size="small" type="primary" :loading="loading" @click="generate">Generate Draft</el-button>
    </div>

    <el-alert v-if="error" type="error" :closable="false" class="mb-3" :title="error" />

    <template v-if="draft">
      <div v-if="draft.linkedin_connect_note" class="mb-3">
        <p class="text-xs font-medium text-slate-600">LinkedIn note</p>
        <el-input type="textarea" :rows="3" readonly :model-value="draft.linkedin_connect_note" />
        <el-button size="small" class="mt-1" @click="copyAll(draft.linkedin_connect_note!)">Copy Draft</el-button>
      </div>
      <div v-if="draft.email_subject || draft.email_body" class="mb-3">
        <p v-if="draft.email_subject" class="text-xs font-medium text-slate-600">Email subject</p>
        <el-input v-if="draft.email_subject" readonly :model-value="draft.email_subject" class="mb-2" />
        <p v-if="draft.email_body" class="text-xs font-medium text-slate-600">Email body</p>
        <el-input v-if="draft.email_body" type="textarea" :rows="6" readonly :model-value="draft.email_body" />
        <el-button
          size="small"
          class="mt-1"
          @click="copyAll([draft.email_subject, draft.email_body].filter(Boolean).join('\n\n'))"
        >
          Copy Draft
        </el-button>
      </div>

      <div class="mb-3 rounded border border-amber-100 bg-amber-50 p-2 text-xs text-amber-900">
        {{ MARK_AS_SENT_HINT }}
      </div>

      <el-button type="success" :loading="marking" :disabled="draftStatus === 'sent'" @click="markAsSent">
        Mark as Sent
      </el-button>

      <p class="mt-2 text-xs text-slate-600">
        <span class="font-medium">Next action after send:</span> {{ pendingNextAction }}
      </p>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchOutreachDraft, type OutreachDraft } from '@/api/outreachDraft'
import { postLeadIntelligenceTouchpoint } from '@/api/aDomain'
import {
  buildManualSentSummary,
  draftStatusLabel,
  followUpNextAction,
  MARK_AS_SENT_HINT,
  OUTREACH_SAFETY_NOTICE,
  touchpointTypeForChannel,
  type DraftStatus,
} from '@/constants/outreachQueue'

const props = defineProps<{
  companyId: string | null
  leadId: string | null
  initialChannel?: string
  initialProductFocus?: string
}>()

const emit = defineEmits<{
  (e: 'use-next-action', value: string): void
  (e: 'marked-sent'): void
  (e: 'draft-status', status: DraftStatus): void
}>()

const loading = ref(false)
const marking = ref(false)
const error = ref('')
const draft = ref<OutreachDraft | null>(null)
const channel = ref(props.initialChannel || 'linkedin_connect')
const productFocus = ref(props.initialProductFocus || 'general')
const draftStatus = ref<DraftStatus>('none')

const pendingNextAction = computed(() =>
  draft.value
    ? followUpNextAction(channel.value, productFocus.value)
    : followUpNextAction(channel.value, productFocus.value),
)

const statusTagType = computed(() => {
  if (draftStatus.value === 'sent') return 'success'
  if (draftStatus.value === 'copied') return 'warning'
  if (draftStatus.value === 'generated') return 'info'
  return 'info'
})

watch(
  () => [props.companyId, props.leadId],
  () => {
    draft.value = null
    error.value = ''
    draftStatus.value = 'none'
    emit('draft-status', 'none')
  },
)

watch(
  () => [props.initialChannel, props.initialProductFocus],
  () => {
    if (props.initialChannel) channel.value = props.initialChannel
    if (props.initialProductFocus) productFocus.value = props.initialProductFocus
  },
)

watch(draftStatus, (s) => emit('draft-status', s))

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
    draftStatus.value = 'generated'
    emit('use-next-action', draft.value.suggested_next_action)
  } catch (e: unknown) {
    error.value = 'Failed to generate draft'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function copyAll(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    if (draftStatus.value !== 'sent') draftStatus.value = 'copied'
    ElMessage.success('Copied to clipboard — paste in LinkedIn or email client')
  } catch {
    ElMessage.warning('Copy failed — select text manually')
  }
}

function draftPreviewText(): string {
  if (!draft.value) return ''
  return (
    draft.value.linkedin_connect_note ||
    [draft.value.email_subject, draft.value.email_body].filter(Boolean).join('\n\n') ||
    ''
  )
}

async function markAsSent() {
  if (!props.leadId || !draft.value) {
    ElMessage.warning('Generate a draft first')
    return
  }
  marking.value = true
  const nextAction = followUpNextAction(channel.value, productFocus.value)
  const interactionType = touchpointTypeForChannel(channel.value)
  const channelName = channel.value.startsWith('linkedin') ? 'linkedin' : 'email'
  try {
    await postLeadIntelligenceTouchpoint(props.leadId, {
      interaction_type: interactionType,
      channel: channelName,
      subject: `Manual outreach — ${channel.value}`,
      summary: buildManualSentSummary({
        channel: channel.value,
        productFocus: productFocus.value,
        draftPreview: draftPreviewText(),
      }),
      next_action: nextAction,
    })
    draftStatus.value = 'sent'
    emit('use-next-action', nextAction)
    emit('marked-sent')
    ElMessage.success('Recorded — touchpoint saved (manual send outside intelliOffice)')
  } catch (e: unknown) {
    ElMessage.error('Failed to record touchpoint')
    console.error(e)
  } finally {
    marking.value = false
  }
}
</script>
