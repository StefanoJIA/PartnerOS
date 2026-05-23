<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { patchLeadFollowUp } from '@/api/aDomain'
import { formatApiError } from '@/api/errors'
import {
  FOLLOW_UP_SCHEDULER_SAFETY,
  quickFollowUpDates,
} from '@/constants/followUpScheduling'

const props = defineProps<{
  leadId: string | null
  initialDate?: string | null
  initialNextAction?: string | null
  suggestedDate?: string | null
}>()

const emit = defineEmits<{
  saved: []
}>()

const saving = ref(false)
const form = reactive({
  nextFollowUpDate: '' as string | null,
  nextAction: '',
})

function resetForm() {
  form.nextFollowUpDate = props.suggestedDate || props.initialDate || ''
  form.nextAction = props.initialNextAction || ''
}

watch(
  () => [props.leadId, props.initialDate, props.initialNextAction, props.suggestedDate],
  () => resetForm(),
  { immediate: true },
)

function applyQuick(key: keyof ReturnType<typeof quickFollowUpDates>) {
  form.nextFollowUpDate = quickFollowUpDates()[key]
}

function clearDate() {
  form.nextFollowUpDate = ''
}

async function save(clearOnly = false) {
  if (!props.leadId) return
  saving.value = true
  try {
    await patchLeadFollowUp(props.leadId, {
      next_follow_up_date: clearOnly ? null : form.nextFollowUpDate || null,
      next_action: form.nextAction.trim() || undefined,
      status_note: clearOnly
        ? 'Follow-up date cleared.'
        : 'Manual follow-up scheduled after outreach.',
      clear_date: clearOnly,
    })
    ElMessage.success(clearOnly ? 'Follow-up date cleared.' : 'Follow-up saved.')
    emit('saved')
  } catch (e) {
    ElMessage.error(formatApiError(e, 'Could not save follow-up.'))
  } finally {
    saving.value = false
  }
}

defineExpose({ applyQuick, form, save, FOLLOW_UP_SCHEDULER_SAFETY })
</script>

<template>
  <el-card v-if="leadId" shadow="never" class="mt-4">
    <template #header>
      <h3 class="text-base font-semibold text-slate-800">Follow-up Scheduler</h3>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-3" :title="FOLLOW_UP_SCHEDULER_SAFETY" />

    <p v-if="suggestedDate && suggestedDate !== form.nextFollowUpDate" class="mb-2 text-xs text-blue-700">
      Suggested: set follow-up date to {{ suggestedDate }} (5 days after Mark as Sent).
    </p>

    <el-form label-position="top" @submit.prevent="save()">
      <el-form-item label="Next follow-up date">
        <el-date-picker
          v-model="form.nextFollowUpDate"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="Select date"
          class="w-full"
        />
      </el-form-item>
      <div class="mb-3 flex flex-wrap gap-1">
        <el-button size="small" @click="applyQuick('tomorrow')">Tomorrow</el-button>
        <el-button size="small" @click="applyQuick('in3Days')">In 3 days</el-button>
        <el-button size="small" @click="applyQuick('in5Days')">In 5 days</el-button>
        <el-button size="small" @click="applyQuick('nextWeek')">Next week</el-button>
        <el-button size="small" @click="clearDate">Clear date</el-button>
      </div>
      <el-form-item label="Next action">
        <el-input v-model="form.nextAction" placeholder="Follow up in 5 days — waiting for email reply" />
      </el-form-item>
      <div class="flex gap-2">
        <el-button type="primary" :loading="saving" @click="save()">Save Follow-up</el-button>
        <el-button :loading="saving" @click="save(true)">Clear saved date</el-button>
      </div>
    </el-form>
  </el-card>
</template>
