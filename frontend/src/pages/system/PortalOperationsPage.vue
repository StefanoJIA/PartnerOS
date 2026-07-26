<template>
  <div class="space-y-4">
    <div class="rounded border border-slate-200 bg-white p-5 shadow-sm">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-blue-600">客户可见桥接</p>
          <h2 class="mt-1 text-2xl font-semibold text-slate-900">Portal 运营</h2>
          <p class="mt-2 max-w-3xl text-sm text-slate-600">
            这里检查客户 Portal 能安全看到什么：订单状态、生产进度、物流计划、资料和反馈入口。它不是内部生产管理页。
          </p>
        </div>
        <el-button type="primary" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="只读运营视图：不会通知客户或供应商，不会调用承运商 API，不会自动改变订单状态。"
    />
    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <el-skeleton v-if="loading && !data" animated :rows="8" />

    <template v-else>
      <section class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div v-for="card in summaryCards" :key="card.label" class="rounded border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm text-slate-500">{{ card.label }}</p>
          <p class="mt-2 text-2xl font-semibold text-slate-900">{{ card.value }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ card.detail }}</p>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4 shadow-sm">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">下一步要补什么</h3>
            <p class="mt-1 text-sm text-slate-500">只显示业务动作，不把底层配置名和技术字段直接堆给运营人员。</p>
          </div>
          <el-tag :type="data?.portal_launch_readiness.ready_for_real_staging ? 'success' : 'warning'" effect="plain">
            {{ data?.portal_launch_readiness.ready_for_real_staging ? '可开始真实联调' : '等待真实联调条件' }}
          </el-tag>
        </div>
        <div class="grid gap-3 md:grid-cols-3">
          <div v-for="item in actionItems" :key="item.title" class="rounded border border-slate-100 bg-slate-50 p-3">
            <div class="flex items-center justify-between gap-2">
              <p class="font-medium text-slate-900">{{ item.title }}</p>
              <el-tag size="small" :type="item.type" effect="plain">{{ item.status }}</el-tag>
            </div>
            <p class="mt-2 text-sm text-slate-600">{{ item.detail }}</p>
          </div>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4 shadow-sm">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">最近客户可见订单</h3>
            <p class="mt-1 text-sm text-slate-500">这些订单会成为客户 Portal 的状态来源；内部成本、利润、供应商备注不会进入这里。</p>
          </div>
          <el-tag effect="plain">{{ data?.recent_customer_visible_orders.total ?? 0 }} 个订单</el-tag>
        </div>
        <el-table :data="data?.recent_customer_visible_orders.items || []" class="w-full" empty-text="暂无客户可见订单">
          <el-table-column label="订单" width="150">
            <template #default="{ row }">
              <el-button link type="primary" @click="openOrder(row.id)">{{ row.order_number }}</el-button>
            </template>
          </el-table-column>
          <el-table-column label="客户" min-width="180">
            <template #default="{ row }">{{ row.company_name || '未关联客户' }}</template>
          </el-table-column>
          <el-table-column label="客户看到的状态" min-width="220">
            <template #default="{ row }">
              <div class="font-medium text-slate-800">{{ row.portal_tracking.label || stageLabel(row.portal_tracking.stage) }}</div>
              <div class="text-xs text-slate-500">{{ row.portal_tracking.next_action_label || '等待内部维护下一步说明' }}</div>
            </template>
          </el-table-column>
          <el-table-column label="可见内容" min-width="240">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tag v-if="row.portal_tracking.has_production_updates" size="small" effect="plain">生产进度</el-tag>
                <el-tag v-if="row.portal_tracking.has_active_shipment" size="small" effect="plain">物流计划 {{ row.portal_tracking.active_shipment_count }}</el-tag>
                <el-tag v-if="row.portal_tracking.has_visible_resources" size="small" effect="plain">资料</el-tag>
                <el-tag v-if="row.portal_tracking.has_open_feedback" size="small" type="warning" effect="plain">反馈 {{ row.portal_tracking.open_feedback_count }}</el-tag>
                <span v-if="!hasPortalSignals(row.portal_tracking)" class="text-sm text-slate-500">待补充客户可见状态</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="130">
            <template #default="{ row }">
              <el-button size="small" @click="openPortalBridge(row.id)">联调检查</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="grid gap-4 xl:grid-cols-2">
        <div class="rounded border border-slate-200 bg-white p-4 shadow-sm">
          <div class="mb-3 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-slate-900">生产 / 物流客户可见摘要</h3>
            <el-tag :type="data?.customer_snapshot_readiness.portal_ready ? 'success' : 'warning'" effect="plain">
              {{ data?.customer_snapshot_readiness.portal_ready ? 'Portal 可展示' : '待补数据' }}
            </el-tag>
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <InfoTile label="有生产进度的订单" :value="data?.customer_snapshot_readiness.production_visible_count ?? 0" />
            <InfoTile label="有物流计划的订单" :value="data?.customer_snapshot_readiness.active_shipment_count ?? 0" />
            <InfoTile label="待发运" :value="data?.customer_snapshot_readiness.ready_to_ship_count ?? 0" />
            <InfoTile label="已发运 / 已送达" :value="`${data?.customer_snapshot_readiness.shipped_count ?? 0} / ${data?.customer_snapshot_readiness.delivered_count ?? 0}`" />
          </div>
          <div v-if="data?.customer_snapshot_readiness.action_items.length" class="mt-4 space-y-2">
            <div v-for="item in data.customer_snapshot_readiness.action_items.slice(0, 5)" :key="`${item.order_id}-${item.stage}`" class="rounded border border-slate-100 bg-slate-50 p-3">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <span class="font-medium text-slate-800">{{ item.order_number || '未关联订单' }} · {{ item.label || stageLabel(item.stage) }}</span>
                <el-button v-if="item.order_id" size="small" @click="openOrder(item.order_id)">打开订单</el-button>
              </div>
              <p class="mt-1 text-sm text-slate-600">{{ businessAction(item.action || item.next_action_label) }}</p>
            </div>
          </div>
        </div>

        <div class="rounded border border-slate-200 bg-white p-4 shadow-sm">
          <div class="mb-3 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-slate-900">反馈与市场信号</h3>
            <el-tag effect="plain">只供内部判断</el-tag>
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <InfoTile label="待处理反馈" :value="data?.feedback_operations.open_count ?? 0" />
            <InfoTile label="高优先级反馈" :value="data?.feedback_operations.high_priority_count ?? 0" />
          </div>
          <div class="mt-4 space-y-2">
            <div v-for="signal in data?.market_signal_preview.items.slice(0, 4) || []" :key="signal.key" class="rounded border border-slate-100 bg-slate-50 p-3">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <span class="font-medium text-slate-800">{{ signal.label }}</span>
                <el-button size="small" @click="openMarketSignal(signal.route_query?.focus_category || signal.key)">复核</el-button>
              </div>
              <p class="mt-1 text-sm text-slate-600">{{ marketSignalText(signal) }}</p>
            </div>
          </div>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4 shadow-sm">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 class="text-lg font-semibold text-slate-900">安全边界</h3>
            <p class="mt-1 text-sm text-slate-500">这里只显示结论，不展示 token、文件路径、内部成本或供应商私密信息。</p>
          </div>
          <el-tag :type="data?.forbidden_field_audit.hits.length ? 'danger' : 'success'" effect="plain">
            {{ data?.forbidden_field_audit.hits.length ? '需要复核' : '未发现禁用字段' }}
          </el-tag>
        </div>
        <div class="grid gap-3 md:grid-cols-3">
          <InfoTile label="自动通知" :value="data?.safety.customer_notified || data?.safety.supplier_notified ? '需检查' : '未触发'" />
          <InfoTile label="承运商 API" :value="data?.safety.carrier_api_called ? '需检查' : '未调用'" />
          <InfoTile label="订单状态自动变更" :value="data?.safety.order_status_mutated ? '需检查' : '未发生'" />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchPortalOperationsConsole, type PortalOperationsConsole } from '@/api/portalOperations'

const InfoTile = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], required: true },
  },
  setup(props) {
    return () =>
      h('div', { class: 'rounded border border-slate-100 bg-slate-50 p-3' }, [
        h('p', { class: 'text-sm text-slate-500' }, props.label),
        h('p', { class: 'mt-1 text-xl font-semibold text-slate-900' }, String(props.value)),
      ])
  },
})

const data = ref<PortalOperationsConsole | null>(null)
const loading = ref(false)
const error = ref('')
const router = useRouter()

const summaryCards = computed(() => [
  {
    label: '联调状态',
    value: data.value?.portal_launch_readiness.ready_for_real_staging ? '可联调' : '待配置',
    detail: data.value?.portal_launch_readiness.ready_for_real_staging ? '真实 staging 条件基本齐备' : '仍缺真实外部配置或签字',
  },
  {
    label: '客户可见订单',
    value: data.value?.recent_customer_visible_orders.total ?? 0,
    detail: '可作为 Portal 订单状态来源',
  },
  {
    label: '生产 / 物流覆盖',
    value: `${data.value?.customer_snapshot_readiness.production_visible_count ?? 0} / ${data.value?.customer_snapshot_readiness.active_shipment_count ?? 0}`,
    detail: '前者为生产进度，后者为物流计划',
  },
  {
    label: '客户反馈',
    value: data.value?.feedback_operations.open_count ?? 0,
    detail: `${data.value?.feedback_operations.high_priority_count ?? 0} 个高优先级`,
  },
])

const actionItems = computed(() => {
  const items = []
  const missing = data.value?.status.missing_config || []
  items.push({
    title: '真实 Portal 配置',
    status: missing.length ? '待补齐' : '已配置',
    type: missing.length ? 'warning' : 'success',
    detail: missing.length ? missing.map(configGapLabel).join('；') : '访问地址、密钥和允许来源已满足当前检查。',
  })
  items.push({
    title: '客户安全字段',
    status: data.value?.forbidden_field_audit.hits.length ? '需复核' : '通过',
    type: data.value?.forbidden_field_audit.hits.length ? 'danger' : 'success',
    detail: data.value?.forbidden_field_audit.hits.length ? '发现可能不应给客户看的字段，需要先处理。' : '未发现成本、利润、token、路径等禁用信息。',
  })
  items.push({
    title: '客户状态内容',
    status: data.value?.customer_snapshot_readiness.portal_ready ? '可展示' : '待维护',
    type: data.value?.customer_snapshot_readiness.portal_ready ? 'success' : 'warning',
    detail: data.value?.customer_snapshot_readiness.portal_ready ? '生产、物流、资料和反馈状态已有客户可读摘要。' : '需要补齐生产节点、物流计划或客户可见说明。',
  })
  return items
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchPortalOperationsConsole()
  } catch (e) {
    console.error('Portal 运营加载失败', e)
    error.value = 'Portal 运营暂时无法加载。请确认后端服务和数据库正在运行，或稍后刷新。'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function configGapLabel(key: string) {
  const labels: Record<string, string> = {
    PORTAL_CUSTOMER_API_ENABLED: '客户 Portal API 未开启',
    PORTAL_CUSTOMER_API_TOKEN: '服务端访问密钥未配置',
    PORTAL_CUSTOMER_ALLOWED_ORIGINS: '允许访问来源未配置',
    PUBLIC_BASE_URL: '公开访问地址未配置',
  }
  return labels[key] || key.replaceAll('_', ' ').toLowerCase()
}

function stageLabel(stage: string | null | undefined) {
  const labels: Record<string, string> = {
    order_received: '已接单',
    supplier_confirmed: '供应商已确认',
    production_in_progress: '生产中',
    ready_to_ship: '待发运',
    shipped: '已发运',
    delivered: '已送达',
    feedback_open: '有反馈待处理',
  }
  return stage ? labels[stage] || stage.replaceAll('_', ' ') : '客户状态待生成'
}

function businessAction(action: string | null | undefined) {
  if (!action) return '请维护下一步客户可见说明。'
  return action
    .replaceAll('review', '复核')
    .replaceAll('shipment', '物流')
    .replaceAll('production', '生产')
    .replaceAll('feedback', '反馈')
    .replaceAll('_', ' ')
}

function marketSignalText(signal: { order_line_count: number; feedback_count: number; delayed_or_blocked_production_count: number; shipment_issue_count: number; review_label: string }) {
  const parts = [
    `${signal.order_line_count} 条订单产品记录`,
    `${signal.feedback_count} 条反馈`,
    `${signal.delayed_or_blocked_production_count} 个生产风险`,
    `${signal.shipment_issue_count} 个物流风险`,
  ]
  return `${signal.review_label}：${parts.join('，')}。`
}

function hasPortalSignals(tracking: { has_production_updates: boolean; has_active_shipment: boolean; has_visible_resources: boolean; has_open_feedback: boolean }) {
  return tracking.has_production_updates || tracking.has_active_shipment || tracking.has_visible_resources || tracking.has_open_feedback
}

function openOrder(orderId: string) {
  router.push({ name: 'order-detail', params: { orderId } })
}

function openPortalBridge(orderId: string) {
  router.push({ name: 'portal-customer-bridge', query: { order_id: orderId } })
}

function openMarketSignal(focusCategory: string) {
  router.push({ name: 'market', query: { focus_category: focusCategory } })
}
</script>
