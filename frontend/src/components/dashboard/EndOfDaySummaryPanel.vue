<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="text-base font-semibold text-slate-800">{{ EOD_TITLE }}</h3>
          <p class="text-xs text-slate-500">{{ EOD_SUBTITLE }}</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <input
            v-model="selectedDate"
            type="date"
            class="rounded border border-slate-200 px-2 py-1 text-sm"
            @change="load"
          />
          <el-button size="small" @click="load">Refresh</el-button>
          <el-button size="small" type="primary" :disabled="!data?.copyable_summary" @click="copySummary">
            Copy Summary
          </el-button>
        </div>
      </div>
    </template>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb-4"
      title="Manual records only"
      :description="EOD_SAFETY_NOTE"
    />

    <el-alert v-if="copyMessage" type="success" :closable="true" class="mb-4" :title="copyMessage" @close="copyMessage = ''" />

    <el-alert
      v-if="error"
      type="error"
      :closable="false"
      show-icon
      class="mb-4"
      title="Summary unavailable"
      :description="error"
    />

    <el-alert
      v-else-if="data?.degraded"
      type="warning"
      :closable="false"
      show-icon
      class="mb-4"
      title="Degraded mode"
      :description="data.warnings?.[0] || EOD_DEGRADED_HINT"
    />

    <template v-if="data && !error">
      <div class="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <SummaryCard label="Manual outreach sent" :value="data.summary.manual_outreach_sent" tone="success" />
        <SummaryCard label="Contact research" :value="data.summary.contact_research_updates" tone="warning" />
        <SummaryCard label="Follow-ups scheduled" :value="data.summary.follow_ups_scheduled" tone="info" />
        <SummaryCard label="Leads touched" :value="data.summary.leads_touched" />
        <SummaryCard label="Overdue remaining" :value="data.summary.overdue_remaining" tone="danger" />
        <SummaryCard label="Due soon" :value="data.summary.due_soon" tone="info" />
      </div>

      <div class="mb-4">
        <p class="mb-2 text-sm font-medium text-slate-700">Highlights</p>
        <ul v-if="data.highlights.length" class="space-y-2 text-sm">
          <li
            v-for="h in data.highlights"
            :key="h.lead_id + h.action"
            class="rounded border border-slate-100 bg-white p-3"
          >
            <span class="font-medium text-slate-800">{{ h.company_name }}</span>
            — {{ h.action }}
            <span v-if="h.next_action" class="text-slate-500"> · Next: {{ h.next_action }}</span>
          </li>
        </ul>
        <p v-else class="text-sm text-slate-500">{{ EOD_EMPTY_HIGHLIGHTS }}</p>
      </div>

      <div>
        <p class="mb-2 text-sm font-medium text-slate-700">Tomorrow Focus</p>
        <ul v-if="data.tomorrow_focus.length" class="space-y-2 text-sm">
          <li
            v-for="t in data.tomorrow_focus"
            :key="t.lead_id"
            class="rounded border border-slate-100 bg-white p-3"
          >
            <span class="font-medium text-slate-800">{{ t.company_name }}</span>
            — {{ t.reason }}
            <span v-if="t.next_action" class="text-slate-500"> · {{ t.next_action }}</span>
          </li>
        </ul>
        <p v-else class="text-sm text-slate-500">{{ EOD_EMPTY_TOMORROW }}</p>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchDailyWorkSummary, type DailyWorkSummary } from '@/api/dailyWorkSummary'
import { formatApiError } from '@/api/errors'
import {
  EOD_DEGRADED_HINT,
  EOD_EMPTY_HIGHLIGHTS,
  EOD_EMPTY_TOMORROW,
  EOD_SAFETY_NOTE,
  EOD_SUBTITLE,
  EOD_TITLE,
  EOD_COPY_SUCCESS,
  todayIsoDate,
} from '@/constants/dailyWorkSummary'
import SummaryCard from './SummaryCard.vue'

const loading = ref(false)
const error = ref<string | null>(null)
const data = ref<DailyWorkSummary | null>(null)
const selectedDate = ref(todayIsoDate())
const copyMessage = ref('')

async function load() {
  loading.value = true
  error.value = null
  try {
    data.value = await fetchDailyWorkSummary(selectedDate.value)
  } catch (e) {
    error.value = formatApiError(e, EOD_DEGRADED_HINT)
    data.value = null
  } finally {
    loading.value = false
  }
}

async function copySummary() {
  if (!data.value?.copyable_summary) return
  try {
    await navigator.clipboard.writeText(data.value.copyable_summary)
    copyMessage.value = EOD_COPY_SUCCESS
  } catch {
    copyMessage.value = 'Copy failed — select text manually from preview below.'
  }
}

onMounted(load)

defineExpose({ load, data, error, loading, copySummary, selectedDate })
</script>
