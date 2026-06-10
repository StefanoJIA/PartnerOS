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
          <el-button size="small" @click="load">刷新</el-button>
          <el-button size="small" type="primary" :disabled="!data?.copyable_summary" @click="copySummary">
            复制总结
          </el-button>
        </div>
      </div>
    </template>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb-4"
      title="仅人工记录"
      :description="EOD_SAFETY_NOTE"
    />

    <el-alert v-if="copyMessage" type="success" :closable="true" class="mb-4" :title="copyMessage" @close="copyMessage = ''" />

    <el-alert
      v-if="error"
      type="error"
      :closable="false"
      show-icon
      class="mb-4"
      title="总结暂不可用"
      :description="error"
    />

    <el-alert
      v-else-if="data?.degraded"
      type="warning"
      :closable="false"
      show-icon
      class="mb-4"
      title="降级模式"
      :description="data.warnings?.[0] || EOD_DEGRADED_HINT"
    />

    <template v-if="data && !error">
      <div class="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <SummaryCard label="已人工触达" :value="data.summary.manual_outreach_sent" tone="success" />
        <SummaryCard label="联系人调研" :value="data.summary.contact_research_updates" tone="warning" />
        <SummaryCard label="已安排跟进" :value="data.summary.follow_ups_scheduled" tone="info" />
        <SummaryCard label="已触达线索" :value="data.summary.leads_touched" />
        <SummaryCard label="剩余逾期" :value="data.summary.overdue_remaining" tone="danger" />
        <SummaryCard label="即将到期" :value="data.summary.due_soon" tone="info" />
      </div>

      <div class="mb-4">
        <p class="mb-2 text-sm font-medium text-slate-700">今日亮点</p>
        <ul v-if="data.highlights.length" class="space-y-2 text-sm">
          <li
            v-for="h in data.highlights"
            :key="h.lead_id + h.action"
            class="rounded border border-slate-100 bg-white p-3"
          >
            <span class="font-medium text-slate-800">{{ h.company_name }}</span>
            — {{ h.action }}
            <span v-if="h.next_action" class="text-slate-500"> · 下一步：{{ h.next_action }}</span>
          </li>
        </ul>
        <p v-else class="text-sm text-slate-500">{{ EOD_EMPTY_HIGHLIGHTS }}</p>
      </div>

      <div>
        <p class="mb-2 text-sm font-medium text-slate-700">明日重点</p>
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
    copyMessage.value = '复制失败，请手动选择下方预览文本。'
  }
}

onMounted(load)

defineExpose({ load, data, error, loading, copySummary, selectedDate })
</script>
