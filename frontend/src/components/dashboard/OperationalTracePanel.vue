<template>
  <section class="rounded border border-slate-200 bg-white p-4">
    <div class="mb-3 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="font-semibold text-slate-800">{{ title }}</h3>
        <p class="mt-1 text-sm text-slate-600">{{ description }}</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <el-tag type="primary" effect="plain">处理记录 {{ records.length }}</el-tag>
        <el-tag type="danger" effect="plain">阻塞 {{ blockedCount }}</el-tag>
        <el-tag type="warning" effect="plain">等外部 {{ waitingExternalCount }}</el-tag>
        <el-tag type="info" effect="plain">逾期 {{ overdueCount }}</el-tag>
      </div>
    </div>
    <el-alert
      class="mb-3"
      type="warning"
      :closable="false"
      show-icon
      title="以下均为 internal handling layer：不代表真实 sign-off、真实 staging evidence 或外部回复，不会改报价/订单/customer-visible 状态。"
    />
    <el-table :data="records" border size="small" :empty-text="emptyText" v-loading="loading">
      <el-table-column label="队列来源" min-width="260">
        <template #default="{ row }">
          <div class="font-medium text-slate-900">{{ row.title }}</div>
          <div class="mt-1 flex flex-wrap gap-1">
            <el-tag size="small" effect="plain">{{ row.priority }}</el-tag>
            <el-tag size="small" effect="plain">{{ row.category }}</el-tag>
            <el-tag size="small" effect="plain">{{ row.source_type }}</el-tag>
          </div>
          <p class="mt-1 text-xs text-slate-500">{{ row.source_path }}</p>
        </template>
      </el-table-column>
      <el-table-column label="处理状态" min-width="220">
        <template #default="{ row }">
          <el-tag :type="statusType(row.handling_status)" effect="plain">{{ statusLabel(row.handling_status) }}</el-tag>
          <p class="mt-2 text-xs text-slate-500">Owner: {{ row.owner || '未指定' }}</p>
          <p v-if="row.follow_up_date" class="mt-1 text-xs text-slate-500">Follow-up: {{ row.follow_up_date }}</p>
        </template>
      </el-table-column>
      <el-table-column label="Partner / Product" min-width="240">
        <template #default="{ row }">
          <div class="text-sm font-medium text-slate-800">{{ row.partner_focus || row.customer_or_account || '内部运营' }}</div>
          <div class="mt-1 flex flex-wrap gap-1">
            <el-tag v-for="item in row.product_focus.slice(0, 6)" :key="item" size="small" effect="plain">{{ item }}</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="阻塞 / 备注 / 决策" min-width="320">
        <template #default="{ row }">
          <p v-if="row.blocked_reason" class="text-xs text-rose-600">阻塞：{{ row.blocked_reason }}</p>
          <p v-if="row.internal_note" class="mt-1 text-xs text-slate-600">备注：{{ row.internal_note }}</p>
          <p v-if="row.decision_summary" class="mt-1 text-xs text-emerald-700">决策：{{ row.decision_summary }}</p>
          <p class="mt-1 text-xs text-slate-400">最近动作：{{ row.last_action || '-' }} / {{ row.updated_at }}</p>
        </template>
      </el-table-column>
      <el-table-column label="入口" width="130" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" plain @click="go(row.source_path)">进入源对象</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchDailyQueueHandling, type DailyQueueHandlingRecord } from '@/api/dashboard'

const props = withDefaults(
  defineProps<{
    title: string
    description: string
    sourceType?: string
    sourceId?: string
    partnerFocus?: string
    category?: string
    emptyText?: string
  }>(),
  {
    sourceType: '',
    sourceId: '',
    partnerFocus: '',
    category: '',
    emptyText: '暂无关联 Daily Queue 处理记录',
  },
)

const router = useRouter()
const loading = ref(false)
const records = ref<DailyQueueHandlingRecord[]>([])
const today = new Date().toISOString().slice(0, 10)

const blockedCount = computed(() => records.value.filter((row) => row.handling_status === 'blocked').length)
const waitingExternalCount = computed(() => records.value.filter((row) => row.handling_status === 'waiting_external').length)
const overdueCount = computed(() => records.value.filter((row) => row.follow_up_date && row.follow_up_date < today).length)

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    new: '未处理',
    acknowledged: '已知晓',
    in_progress: '处理中',
    deferred: '已延期',
    blocked: '处理阻塞',
    waiting_external: '等待外部输入',
    decision_recorded: '已记录内部决策',
  }
  return labels[status] || status
}

function statusType(status: string) {
  if (status === 'blocked') return 'danger'
  if (status === 'waiting_external' || status === 'deferred') return 'warning'
  if (status === 'in_progress' || status === 'decision_recorded') return 'success'
  return 'info'
}

function go(path: string) {
  router.push(path)
}

async function load() {
  loading.value = true
  try {
    records.value = await fetchDailyQueueHandling({
      source_type: props.sourceType || undefined,
      source_id: props.sourceId || undefined,
      partner_focus: props.partnerFocus || undefined,
      category: props.category || undefined,
    })
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => [props.sourceType, props.sourceId, props.partnerFocus, props.category], load)
</script>
