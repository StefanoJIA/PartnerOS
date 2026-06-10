<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="text-base font-semibold text-slate-800">{{ DAILY_OPS_TITLE }}</h3>
          <p class="text-xs text-slate-500">{{ DAILY_OPS_SUBTITLE }}</p>
        </div>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
    </template>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb-4"
      title="仅人工流程"
      :description="DAILY_OPS_SAFETY_NOTE"
    />

    <el-alert
      v-if="error"
      type="error"
      :closable="false"
      show-icon
      class="mb-4"
      title="每日运营暂不可用"
      :description="error"
    />

    <el-alert
      v-else-if="data?.degraded"
      type="warning"
      :closable="false"
      show-icon
      class="mb-4"
      title="降级模式"
      :description="data.warnings?.[0] || DAILY_OPS_DEGRADED_HINT"
    />

    <template v-if="data && !error">
      <div class="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          label="已逾期"
          :value="data.summary.overdue"
          tone="danger"
          :to="SUMMARY_CARD_LINKS['Overdue']"
        />
        <SummaryCard
          label="今日到期"
          :value="data.summary.due_today"
          tone="warning"
          :to="SUMMARY_CARD_LINKS['Due Today']"
        />
        <SummaryCard
          label="即将到期"
          :value="data.summary.due_soon"
          tone="info"
          :to="SUMMARY_CARD_LINKS['Due Soon']"
        />
        <SummaryCard
          label="高优先级"
          :value="data.summary.high_priority"
          tone="primary"
          :to="SUMMARY_CARD_LINKS['High Priority']"
        />
        <SummaryCard
          label="需联系人调研"
          :value="data.summary.needs_contact_research"
          :to="SUMMARY_CARD_LINKS['Needs Contact Research']"
        />
        <SummaryCard
          label="可触达"
          :value="data.summary.ready_for_outreach"
          :to="SUMMARY_CARD_LINKS['Ready for Outreach']"
        />
        <SummaryCard
          label="等待回复"
          :value="data.summary.waiting_reply"
          :to="SUMMARY_CARD_LINKS['Waiting Reply']"
        />
        <SummaryCard
          label="需补全资料"
          :value="data.summary.needs_enrichment"
          :to="SUMMARY_CARD_LINKS['Needs Enrichment']"
        />
      </div>

      <div class="mb-4">
        <p class="mb-2 text-sm font-medium text-slate-700">快捷动作</p>
        <div class="flex flex-wrap gap-2">
          <router-link v-for="a in data.quick_actions" :key="a.path" :to="a.path">
            <el-button size="small">{{ a.label }}</el-button>
          </router-link>
        </div>
      </div>

      <div class="mb-4">
        <p class="mb-2 text-sm font-medium text-slate-700">今日重点</p>
        <el-table v-if="data.today_focus.length" :data="data.today_focus" size="small" stripe>
          <el-table-column prop="company_name" label="公司" min-width="140" />
          <el-table-column prop="reason" label="原因" min-width="160" />
          <el-table-column label="分组" min-width="120">
            <template #default="{ row }">
              <span class="text-xs">{{ (row.segments || []).slice(0, 2).join(', ') || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="到期状态" width="110">
            <template #default="{ row }">{{ zhLabel(DUE_STATUS_LABELS, row.due_status, '未设置') }}</template>
          </el-table-column>
          <el-table-column prop="next_action" label="下一步" min-width="140" show-overflow-tooltip />
          <el-table-column label="" width="100" fixed="right">
            <template #default="{ row }">
              <router-link :to="{ path: '/lead-intelligence', query: { leadId: row.lead_id } }">
                <el-button size="small" type="primary" link>打开线索</el-button>
              </router-link>
            </template>
          </el-table-column>
        </el-table>
        <p v-else class="text-sm text-slate-500">暂无今日重点，请导入线索或安排跟进。</p>
      </div>

      <div class="mb-4 grid gap-4 lg:grid-cols-2">
        <div>
          <RecentActivityList
            title="近期人工触达"
            :items="manualOutreach"
            :empty-text="RECENT_OUTREACH_EMPTY"
          />
        </div>
        <div>
          <RecentActivityList
            title="近期联系人调研"
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
import { DUE_STATUS_LABELS, zhLabel } from '@/copy/zhCN'
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
