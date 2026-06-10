<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { postContactResearch, type ContactResearchPayload } from '@/api/aDomain'
import { formatApiError } from '@/api/errors'
import { MISSING_FIELD_LABELS, type CompletenessRow } from '@/constants/leadCompleteness'

export type ContactResearchInitial = {
  website?: string | null
  companyType?: string | null
  companyNotes?: string | null
  contactName?: string | null
  contactTitle?: string | null
  contactEmail?: string | null
  contactPhone?: string | null
  linkedinUrl?: string | null
  nextAction?: string | null
}

const props = defineProps<{
  visible: boolean
  row: CompletenessRow | null
  initial: ContactResearchInitial | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: []
}>()

const saving = ref(false)

const form = reactive({
  website: '',
  companyType: '',
  notes: '',
  contactName: '',
  contactTitle: '',
  contactEmail: '',
  contactPhone: '',
  linkedinUrl: '',
  nextAction: '',
  touchpointNote: '已人工更新联系人调研信息。',
})

const SAFETY_NOTICE =
  '此工具只记录人工调研结果，不会搜索 LinkedIn、抓取网站或自动发送消息。'

const missingLabels = computed(() =>
  (props.row?.missingFields || []).map((f) => MISSING_FIELD_LABELS[f] || f).join(', '),
)

function resetForm() {
  const init = props.initial
  form.website = init?.website && init.website !== '—' ? init.website : ''
  form.companyType = init?.companyType && init.companyType !== '—' ? init.companyType : ''
  form.notes = ''
  form.contactName = init?.contactName && init.contactName !== '—' ? init.contactName : ''
  form.contactTitle = init?.contactTitle || ''
  form.contactEmail = init?.contactEmail || ''
  form.contactPhone = init?.contactPhone || ''
  form.linkedinUrl = init?.linkedinUrl || ''
  const na = init?.nextAction || ''
  form.nextAction = na && na !== 'No next action set.' ? na : ''
  form.touchpointNote = '已人工更新联系人调研信息。'
}

watch(
  () => props.visible,
  (open) => {
    if (open) resetForm()
  },
)

function close() {
  emit('update:visible', false)
}

function buildPayload(): ContactResearchPayload {
  const payload: ContactResearchPayload = {}
  const company: ContactResearchPayload['company'] = {}
  if (form.website.trim()) company.website = form.website.trim()
  if (form.companyType.trim()) company.company_type = form.companyType.trim()
  if (form.notes.trim()) company.notes = form.notes.trim()
  if (Object.keys(company).length) payload.company = company

  const contact: ContactResearchPayload['contact'] = {}
  if (form.contactName.trim()) contact.name = form.contactName.trim()
  if (form.contactTitle.trim()) contact.title = form.contactTitle.trim()
  if (form.contactEmail.trim()) contact.email = form.contactEmail.trim()
  if (form.contactPhone.trim()) contact.phone = form.contactPhone.trim()
  if (form.linkedinUrl.trim()) contact.linkedin_url = form.linkedinUrl.trim()
  if (Object.keys(contact).length) payload.contact = contact

  if (form.nextAction.trim()) {
    payload.lead = { next_action: form.nextAction.trim() }
  }
  if (form.touchpointNote.trim()) {
    payload.touchpoint_note = form.touchpointNote.trim()
  }
  return payload
}

async function save() {
  if (!props.row?.leadId) return
  saving.value = true
  try {
    await postContactResearch(props.row.leadId, buildPayload())
    ElMessage.success('联系人调研已保存。')
    emit('saved')
    close()
  } catch (e) {
    ElMessage.error(formatApiError(e, '联系人调研保存失败。'))
  } finally {
    saving.value = false
  }
}

defineExpose({ save, buildPayload, form, SAFETY_NOTICE })
</script>

<template>
  <el-drawer
    :model-value="visible"
    title="联系人调研"
    size="480px"
    :append-to-body="false"
    destroy-on-close
    @update:model-value="emit('update:visible', $event)"
  >
    <template v-if="row">
      <p class="text-sm font-medium text-slate-800">{{ row.companyName }}</p>
      <p class="mt-1 text-xs text-slate-500">
        完整度分数：<span class="font-semibold">{{ row.score }}</span>
        · {{ row.statusLabel }}
      </p>
      <p v-if="missingLabels" class="mt-2 text-xs text-amber-700">缺失字段：{{ missingLabels }}</p>
      <p class="mt-1 text-xs text-slate-600">{{ row.recommendedResearchAction }}</p>

      <el-alert type="info" :closable="false" show-icon class="my-4" :title="SAFETY_NOTICE" />

      <el-form label-position="top" class="space-y-1" @submit.prevent="save">
        <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">公司</p>
        <el-form-item label="官网">
          <el-input v-model="form.website" placeholder="https://example.com" />
        </el-form-item>
        <el-form-item label="公司类型">
          <el-input v-model="form.companyType" placeholder="Office Furniture Dealer" />
        </el-form-item>
        <el-form-item label="调研备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="追加到公司备注" />
        </el-form-item>

        <p class="pt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">联系人</p>
        <el-form-item label="联系人姓名">
          <el-input v-model="form.contactName" placeholder="First Last" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="form.contactTitle" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.contactEmail" type="email" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.contactPhone" />
        </el-form-item>
        <el-form-item label="LinkedIn URL">
          <el-input v-model="form.linkedinUrl" placeholder="https://linkedin.com/in/..." />
        </el-form-item>

        <p class="pt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">线索</p>
        <el-form-item label="下一步动作">
          <el-input v-model="form.nextAction" placeholder="触达前先调研联系人" />
        </el-form-item>

        <div class="mt-4 flex gap-2">
          <el-button type="primary" :loading="saving" @click="save">保存调研更新</el-button>
          <el-button @click="close">取消</el-button>
        </div>
      </el-form>
    </template>
  </el-drawer>
</template>
