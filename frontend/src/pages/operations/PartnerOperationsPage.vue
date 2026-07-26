<template>
  <div class="space-y-4">
    <div class="rounded border border-slate-200 bg-white p-5 shadow-sm">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-blue-600">内部交付协同</p>
          <h1 class="mt-1 text-2xl font-semibold text-slate-900">生产与物流摘要</h1>
          <p class="mt-2 max-w-3xl text-sm text-slate-600">
            这里看的是内部执行：Partner 分单、供应商确认、生产节点和物流计划。它不是客户 Portal 页面，也不会通知客户或供应商。
          </p>
        </div>
        <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <el-alert
      v-if="dashboard?.safety.read_only"
      type="info"
      :closable="false"
      show-icon
      title="只读摘要：本页不会通知供应商或客户，不会创建物流，不会自动改变订单状态。"
    />

    <el-skeleton v-if="loading && !dashboard" animated :rows="6" />
    <el-alert v-else-if="error" type="error" :closable="false" show-icon :title="error" />

    <template v-else-if="dashboard">
      <section class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div v-for="metric in metrics" :key="metric.label" class="rounded border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm text-slate-500">{{ metric.label }}</p>
          <p class="mt-2 text-2xl font-semibold text-slate-900">{{ metric.value }}</p>
          <p v-if="metric.detail" class="mt-1 text-xs text-slate-500">{{ metric.detail }}</p>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4 shadow-sm">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Partner 承接与交付风险</h2>
            <p class="mt-1 text-sm text-slate-500">按 Partner 汇总当前订单、生产和物流状态，只显示运营能直接处理的语言。</p>
          </div>
          <el-tag effect="plain">{{ dashboard.total }} 个 Partner</el-tag>
        </div>

        <el-table :data="dashboard.items" class="w-full" empty-text="暂无 Partner 分单">
          <el-table-column label="Partner" min-width="210">
            <template #default="{ row }">
              <div class="font-medium text-slate-900">{{ row.partner_name }}</div>
              <div class="text-xs text-slate-500">{{ partnerTypeLabel(row.partner_type) }}</div>
            </template>
          </el-table-column>
          <el-table-column label="承接范围" min-width="170">
            <template #default="{ row }">
              <div>{{ row.order_count }} 个订单 / {{ row.split_count }} 个分单</div>
              <div class="text-xs text-slate-500">{{ row.line_item_count }} 个产品行</div>
            </template>
          </el-table-column>
          <el-table-column label="供应商确认" min-width="180">
            <template #default="{ row }">
              <StatusChips :counts="row.supplier_confirmation_status_counts" />
            </template>
          </el-table-column>
          <el-table-column label="生产进度" min-width="210">
            <template #default="{ row }">
              <StatusChips :counts="row.milestone_status_counts" />
              <div v-if="row.delayed_milestone_count || row.blocked_milestone_count" class="mt-1 text-xs text-amber-700">
                延迟 {{ row.delayed_milestone_count }} / 阻塞 {{ row.blocked_milestone_count }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="物流计划" min-width="170">
            <template #default="{ row }">
              <StatusChips :counts="row.shipment_status_counts" />
              <div class="mt-1 text-xs text-slate-500">进行中 {{ row.active_shipment_count }}</div>
            </template>
          </el-table-column>
          <el-table-column label="预计就绪" width="130">
            <template #default="{ row }">{{ row.next_expected_ready_date || '待维护' }}</template>
          </el-table-column>
          <el-table-column label="需要处理" min-width="230">
            <template #default="{ row }">
              <div v-if="row.risk_flags.length" class="flex flex-wrap gap-1">
                <el-tag v-for="flag in row.risk_flags" :key="flag" type="warning" size="small" effect="plain">
                  {{ riskFlagLabel(flag) }}
                </el-tag>
              </div>
              <span v-else class="text-sm text-slate-500">暂无明显风险</span>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { ElTag } from 'element-plus'
import { fetchPartnerOperationsDashboard, type PartnerOperationsDashboard } from '@/api/operations'

const dashboard = ref<PartnerOperationsDashboard | null>(null)
const loading = ref(false)
const error = ref('')

const STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  draft: '草稿',
  requested: '已请求',
  confirmed: '已确认',
  declined: '未承接',
  planned: '计划中',
  in_progress: '进行中',
  completed: '已完成',
  delayed: '延迟',
  blocked: '阻塞',
  cancelled: '已取消',
  booked: '已订舱',
  in_transit: '运输中',
  shipped: '已发运',
  delivered: '已交付',
}

const StatusChips = defineComponent({
  props: {
    counts: { type: Object, required: true },
  },
  setup(props) {
    return () => {
      const entries = Object.entries(props.counts as Record<string, number>).filter(([, value]) => value > 0)
      if (!entries.length) return h('span', { class: 'text-sm text-slate-500' }, '暂无记录')
      return h(
        'div',
        { class: 'flex flex-wrap gap-1' },
        entries.map(([key, value]) =>
          h(
            ElTag,
            { key, size: 'small', type: key.includes('delayed') || key.includes('blocked') ? 'warning' : 'info', effect: 'plain' },
            () => `${statusLabel(key)} ${value}`,
          ),
        ),
      )
    }
  },
})

const metrics = computed(() => {
  const summary = dashboard.value?.summary
  if (!summary) return []
  return [
    { label: '参与 Partner', value: summary.partner_count, detail: '当前有承接关系的制造伙伴' },
    { label: '订单覆盖', value: summary.order_count, detail: `${summary.split_count} 个分单` },
    { label: '供应商待确认', value: summary.supplier_open_split_count, detail: `${summary.supplier_confirmed_split_count} 个已确认` },
    { label: '生产风险', value: `${summary.delayed_milestone_count + summary.blocked_milestone_count}`, detail: '延迟或阻塞节点' },
    { label: '物流进行中', value: summary.active_shipment_count, detail: '已有物流计划但未完成' },
    { label: '已发运/已交付', value: summary.shipped_or_delivered_count, detail: '进入客户可见交付阶段' },
  ]
})

function statusLabel(status: string) {
  return STATUS_LABELS[status] || status.replaceAll('_', ' ')
}

function partnerTypeLabel(type: string | null) {
  if (!type) return '未分类 Partner'
  const labels: Record<string, string> = {
    manufacturer: '制造商',
    supplier: '供应商',
    logistics: '物流伙伴',
  }
  return labels[type] || type
}

function riskFlagLabel(flag: string) {
  const labels: Record<string, string> = {
    supplier_confirmation_open: '供应商待确认',
    delayed_milestones: '生产节点延迟',
    blocked_milestones: '生产节点阻塞',
    shipment_not_planned: '物流未规划',
    shipment_delayed: '物流延迟',
    missing_ready_date: '预计就绪日期缺失',
  }
  return labels[flag] || flag.replaceAll('_', ' ')
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    dashboard.value = await fetchPartnerOperationsDashboard()
  } catch (err) {
    console.error('生产与物流摘要加载失败', err)
    error.value = '生产与物流摘要暂时无法加载。请确认后端服务和数据库正在运行，或稍后刷新。'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
