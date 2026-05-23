<script setup lang="ts">
import { ref, watch } from 'vue'
import { fetchLeadTimeline, type LeadTimeline } from '@/api/aDomain'
import { formatApiError } from '@/api/errors'
import {
  TIMELINE_EMPTY_MESSAGE,
  TIMELINE_SAFETY_NOTICE,
  followUpHintTagType,
  formatTimelineTimestamp,
  interactionTypeBadgeType,
} from '@/constants/outreachTimeline'

const props = defineProps<{
  leadId: string | null
}>()

const timeline = ref<LeadTimeline | null>(null)
const loading = ref(false)
const error = ref('')

async function reload() {
  if (!props.leadId) {
    timeline.value = null
    return
  }
  loading.value = true
  error.value = ''
  try {
    timeline.value = await fetchLeadTimeline(props.leadId)
  } catch (e) {
    error.value = formatApiError(e, 'Could not load outreach history.')
    timeline.value = null
  } finally {
    loading.value = false
  }
}

watch(
  () => props.leadId,
  () => {
    void reload()
  },
  { immediate: true },
)

defineExpose({ reload })
</script>

<template>
  <el-card v-loading="loading" shadow="never" class="mt-4">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h3 class="text-base font-semibold text-slate-800">Outreach History</h3>
        <el-button v-if="leadId" size="small" @click="reload">Refresh</el-button>
      </div>
    </template>

    <el-alert type="info" :closable="false" show-icon class="mb-3" :title="TIMELINE_SAFETY_NOTICE" />

    <el-alert
      v-if="error"
      type="warning"
      :closable="false"
      show-icon
      class="mb-3"
      title="Could not load timeline"
      :description="error"
    />

    <template v-if="timeline">
      <div class="mb-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <div class="rounded border border-slate-200 bg-slate-50 px-2 py-2">
          <p class="text-xs text-slate-500">Company</p>
          <p class="font-medium text-slate-800">{{ timeline.company_name }}</p>
        </div>
        <div class="rounded border border-slate-200 bg-slate-50 px-2 py-2">
          <p class="text-xs text-slate-500">Total touchpoints</p>
          <p class="font-medium text-slate-800">{{ timeline.stats.total_touchpoints }}</p>
        </div>
        <div class="rounded border border-slate-200 bg-slate-50 px-2 py-2">
          <p class="text-xs text-slate-500">Last touchpoint</p>
          <p class="font-medium text-slate-800">{{ formatTimelineTimestamp(timeline.last_touchpoint_at) }}</p>
        </div>
        <div class="rounded border border-slate-200 bg-slate-50 px-2 py-2">
          <p class="text-xs text-slate-500">Follow-up hint</p>
          <el-tag size="small" :type="followUpHintTagType(timeline.follow_up_hint)" effect="plain">
            {{ timeline.follow_up_hint }}
          </el-tag>
        </div>
      </div>

      <p v-if="timeline.next_action" class="mb-3 text-sm text-slate-600">
        <span class="font-medium">Next action:</span> {{ timeline.next_action }}
      </p>

      <div v-if="timeline.items.length" class="space-y-3">
        <div
          v-for="item in timeline.items"
          :key="item.id"
          class="rounded border border-slate-200 bg-white px-3 py-2"
        >
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-xs text-slate-500">{{ formatTimelineTimestamp(item.timestamp) }}</span>
            <el-tag
              size="small"
              :type="interactionTypeBadgeType(item.type, item.is_manual_send, item.is_contact_research)"
              effect="plain"
            >
              {{ item.type.replace(/_/g, ' ') }}
            </el-tag>
            <el-tag v-if="item.channel" size="small" type="info" effect="plain">{{ item.channel }}</el-tag>
            <el-tag v-if="item.is_manual_send" size="small" type="success" effect="dark">Manual send</el-tag>
            <el-tag v-if="item.is_contact_research" size="small" type="warning" effect="dark">Contact research</el-tag>
          </div>
          <p class="mt-1 text-sm font-medium text-slate-800">{{ item.title }}</p>
          <p v-if="item.summary" class="mt-1 text-xs text-slate-600">{{ item.summary }}</p>
        </div>
      </div>

      <el-empty v-else :description="TIMELINE_EMPTY_MESSAGE" />
    </template>

    <p v-else-if="!leadId" class="text-sm text-slate-500">Select a lead to view outreach history.</p>
  </el-card>
</template>
