<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="text-base font-semibold text-slate-800">Daily Operations</h3>
          <p class="text-xs text-slate-500">
            Your daily manual outreach and follow-up command center.
          </p>
        </div>
        <el-button size="small" @click="load">Refresh</el-button>
      </div>
    </template>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb-4"
      title="Manual workflow only"
      :description="DAILY_OPS_SAFETY_NOTE"
    />

    <el-alert
      v-if="error"
      type="error"
      :closable="false"
      show-icon
      class="mb-4"
      title="Daily operations unavailable"
      :description="error"
    />

    <el-alert
      v-else-if="data?.degraded"
      type="warning"
      :closable="false"
      show-icon
      class="mb-4"
      title="Degraded mode"
      :description="data.warnings?.[0] || DAILY_OPS_DEGRADED_HINT"
    />

    <template v-if="data && !error">
      <div class="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard label="Overdue" :value="data.summary.overdue" tone="danger" />
        <SummaryCard label="Due Today" :value="data.summary.due_today" tone="warning" />
        <SummaryCard label="Due Soon" :value="data.summary.due_soon" tone="info" />
        <SummaryCard label="High Priority" :value="data.summary.high_priority" tone="primary" />
        <SummaryCard label="Needs Contact Research" :value="data.summary.needs_contact_research" />
        <SummaryCard label="Ready for Outreach" :value="data.summary.ready_for_outreach" />
        <SummaryCard label="Waiting Reply" :value="data.summary.waiting_reply" />
        <SummaryCard label="Needs Enrichment" :value="data.summary.needs_enrichment" />
      </div>

      <div class="mb-4">
        <p class="mb-2 text-sm font-medium text-slate-700">Quick Actions</p>
        <div class="flex flex-wrap gap-2">
          <router-link v-for="a in data.quick_actions" :key="a.path" :to="a.path">
            <el-button size="small">{{ a.label }}</el-button>
          </router-link>
        </div>
      </div>

      <div class="mb-4">
        <p class="mb-2 text-sm font-medium text-slate-700">Today Focus</p>
        <el-table v-if="data.today_focus.length" :data="data.today_focus" size="small" stripe>
          <el-table-column prop="company_name" label="Company" min-width="140" />
          <el-table-column prop="reason" label="Reason" min-width="160" />
          <el-table-column label="Segment" min-width="120">
            <template #default="{ row }">
              <span class="text-xs">{{ (row.segments || []).slice(0, 2).join(', ') || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="due_status" label="Due status" width="110" />
          <el-table-column prop="next_action" label="Next action" min-width="140" show-overflow-tooltip />
          <el-table-column label="" width="100" fixed="right">
            <template #default="{ row }">
              <router-link :to="{ path: '/lead-intelligence', query: { leadId: row.lead_id } }">
                <el-button size="small" type="primary" link>Open Lead</el-button>
              </router-link>
            </template>
          </el-table-column>
        </el-table>
        <p v-else class="text-sm text-slate-500">No focus items — import leads or schedule follow-ups.</p>
      </div>

      <div v-if="data.recent_outreach.length">
        <p class="mb-2 text-sm font-medium text-slate-700">Recent Manual Outreach</p>
        <el-table :data="data.recent_outreach" size="small" stripe>
          <el-table-column prop="company_name" label="Company" min-width="120" />
          <el-table-column prop="interaction_type" label="Type" width="100" />
          <el-table-column prop="channel" label="Channel" width="100" />
          <el-table-column label="Time" width="160">
            <template #default="{ row }">
              <span class="text-xs">{{ formatTime(row.timestamp) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="next_action" label="Next action" min-width="140" show-overflow-tooltip />
        </el-table>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchDailyOpsSummary, type DailyOpsSummary } from '@/api/dailyOps'
import { formatApiError } from '@/api/errors'
import { DAILY_OPS_DEGRADED_HINT, DAILY_OPS_SAFETY_NOTE } from '@/constants/dailyOps'
import SummaryCard from './SummaryCard.vue'

const loading = ref(false)
const error = ref<string | null>(null)
const data = ref<DailyOpsSummary | null>(null)

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  try {
    return iso.slice(0, 16).replace('T', ' ')
  } catch {
    return iso
  }
}

async function load() {
  loading.value = true
  error.value = null
  try {
    data.value = await fetchDailyOpsSummary()
  } catch (e) {
    error.value = formatApiError(e, DAILY_OPS_DEGRADED_HINT)
    data.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)

defineExpose({ load, data, error, loading })
</script>
