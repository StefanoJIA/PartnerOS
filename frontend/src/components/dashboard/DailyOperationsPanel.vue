<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="text-base font-semibold text-slate-800">{{ DAILY_OPS_TITLE }}</h3>
          <p class="text-xs text-slate-500">{{ DAILY_OPS_SUBTITLE }}</p>
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
        <SummaryCard
          label="Overdue"
          :value="data.summary.overdue"
          tone="danger"
          :to="SUMMARY_CARD_LINKS['Overdue']"
        />
        <SummaryCard
          label="Due Today"
          :value="data.summary.due_today"
          tone="warning"
          :to="SUMMARY_CARD_LINKS['Due Today']"
        />
        <SummaryCard
          label="Due Soon"
          :value="data.summary.due_soon"
          tone="info"
          :to="SUMMARY_CARD_LINKS['Due Soon']"
        />
        <SummaryCard
          label="High Priority"
          :value="data.summary.high_priority"
          tone="primary"
          :to="SUMMARY_CARD_LINKS['High Priority']"
        />
        <SummaryCard
          label="Needs Contact Research"
          :value="data.summary.needs_contact_research"
          :to="SUMMARY_CARD_LINKS['Needs Contact Research']"
        />
        <SummaryCard
          label="Ready for Outreach"
          :value="data.summary.ready_for_outreach"
          :to="SUMMARY_CARD_LINKS['Ready for Outreach']"
        />
        <SummaryCard
          label="Waiting Reply"
          :value="data.summary.waiting_reply"
          :to="SUMMARY_CARD_LINKS['Waiting Reply']"
        />
        <SummaryCard
          label="Needs Enrichment"
          :value="data.summary.needs_enrichment"
          :to="SUMMARY_CARD_LINKS['Needs Enrichment']"
        />
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

      <div class="mb-4 grid gap-4 lg:grid-cols-2">
        <div>
          <RecentActivityList
            title="Recent Manual Outreach"
            :items="manualOutreach"
            :empty-text="RECENT_OUTREACH_EMPTY"
          />
        </div>
        <div>
          <RecentActivityList
            title="Recent Contact Research"
            :items="contactResearch"
            :empty-text="RECENT_RESEARCH_EMPTY"
          />
        </div>
      </div>

      <DashboardSystemStrip class="mt-2" />
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchDailyOpsSummary, type DailyOpsSummary } from '@/api/dailyOps'
import { formatApiError } from '@/api/errors'
import {
  DAILY_OPS_DEGRADED_HINT,
  DAILY_OPS_SAFETY_NOTE,
  DAILY_OPS_SUBTITLE,
  DAILY_OPS_TITLE,
  RECENT_OUTREACH_EMPTY,
  RECENT_RESEARCH_EMPTY,
  SUMMARY_CARD_LINKS,
} from '@/constants/dailyOps'
import SummaryCard from './SummaryCard.vue'
import RecentActivityList from './RecentActivityList.vue'
import DashboardSystemStrip from './DashboardSystemStrip.vue'

const loading = ref(false)
const error = ref<string | null>(null)
const data = ref<DailyOpsSummary | null>(null)

const manualOutreach = computed(
  () => data.value?.recent_manual_outreach ?? data.value?.recent_outreach ?? [],
)
const contactResearch = computed(() => data.value?.recent_contact_research ?? [])

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
