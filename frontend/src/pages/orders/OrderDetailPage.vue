<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ensureProductionMilestones,
  fetchOrder,
  fetchOrderConfirmations,
  fetchPartnerSplits,
  fetchProductionMilestones,
  fetchShipmentPlans,
  updateProductionMilestone,
  updateShipmentPlan,
  type OrderConfirmationRecord,
  type OrderDetail,
  type PartnerSplit,
  type ProductionMilestone,
  type ShipmentPlan,
} from '@/api/orders'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const actionLoading = ref(false)
const error = ref('')
const successMsg = ref('')
const order = ref<OrderDetail | null>(null)
const confirmations = ref<OrderConfirmationRecord[]>([])
const partnerSplits = ref<PartnerSplit[]>([])
const milestones = ref<ProductionMilestone[]>([])
const shipmentPlans = ref<ShipmentPlan[]>([])

const ORDER_STATUS: Record<string, string> = {
  pending_customer_confirmation: '待客户确认',
  confirmed: '已确认',
  supplier_confirmation_pending: '待供应商确认',
  supplier_confirmed: '供应商已确认',
  production_pending: '待生产',
  in_production: '生产中',
  ready_to_ship: '待发运',
  shipped: '已发运',
  delivered: '已交付',
  on_hold: '暂停',
  cancelled: '已取消',
}

const SHIPMENT_STATUS: Record<string, string> = {
  draft: '草稿',
  planned: '已计划',
  booked: '已订舱',
  in_transit: '运输中',
  shipped: '已发运',
  delivered: '已交付',
  delayed: '延误',
  cancelled: '已取消',
}

const SUPPLIER_STATUS: Record<string, string> = {
  pending: '待确认',
  confirmed: '已确认',
  partially_confirmed: '部分确认',
  needs_clarification: '需澄清',
  rejected: '已拒绝',
  in_production: '生产中',
}

const MILESTONE_TYPE_LABELS: Record<string, string> = {
  order_received: '订单接收',
  supplier_confirmed: '供应商确认',
  materials_prepared: '备料',
  cutting: '切割',
  welding: '焊接 / 打磨',
  painting: '喷涂',
  assembly: '组装',
  quality_check: '测试 / 质检',
  packing: '打包',
  ready_to_ship: '出厂 / 待发运',
  production_started: '生产开始',
  production_pending: '待生产',
}

const safetyNote =
  '本页只维护内部订单执行记录。更新生产或物流状态不会自动通知客户/供应商，不会调用承运商 API，也不会自动改变客户订单状态。'

const visibleMilestones = computed(() =>
  [...milestones.value].sort((a, b) => Number(a.sequence || 0) - Number(b.sequence || 0)),
)

const currentMilestone = computed(() => {
  return (
    visibleMilestones.value.find((item) => item.status === 'in_progress') ||
    visibleMilestones.value.find((item) => ['planned', 'pending', 'delayed', 'blocked'].includes(item.status)) ||
    visibleMilestones.value[visibleMilestones.value.length - 1] ||
    null
  )
})

const completedMilestoneCount = computed(() => visibleMilestones.value.filter((item) => item.status === 'completed').length)

const activeShipment = computed(() => {
  return shipmentPlans.value.find((item) => item.status !== 'cancelled') || shipmentPlans.value[0] || null
})

const executionStage = computed(() => {
  if (!order.value) return '未加载'
  if (activeShipment.value?.status === 'delivered') return '已交付'
  if (['shipped', 'in_transit'].includes(activeShipment.value?.status || '')) return '运输中'
  if (currentMilestone.value?.milestone_type === 'ready_to_ship' && currentMilestone.value.status === 'completed') return '待发运'
  if (currentMilestone.value) return `生产节点：${milestoneName(currentMilestone.value)}`
  return label(ORDER_STATUS, order.value.status)
})

function label(map: Record<string, string>, value: string | null | undefined, fallback = '未设置') {
  if (!value) return fallback
  return map[value] || value
}

function milestoneName(item: ProductionMilestone) {
  return MILESTONE_TYPE_LABELS[item.milestone_type] || item.milestone_label || item.milestone_type
}

function formatMoney(value: string | number | null | undefined, currency = 'USD') {
  const n = Number(value || 0)
  return `${currency} ${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatDate(value: string | null | undefined) {
  if (!value) return '-'
  return value.slice(0, 10)
}

function statusClass(status: string | null | undefined) {
  if (status === 'completed' || status === 'delivered' || status === 'confirmed') return 'is-done'
  if (status === 'in_progress' || status === 'planned' || status === 'shipped' || status === 'in_transit') return 'is-active'
  if (status === 'delayed' || status === 'blocked') return 'is-risk'
  return 'is-muted'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const id = route.params.orderId as string
    order.value = await fetchOrder(id)
    const [confirmationData, splitData, milestoneData, shipmentData] = await Promise.all([
      fetchOrderConfirmations(id),
      fetchPartnerSplits(id),
      fetchProductionMilestones(id),
      fetchShipmentPlans(id),
    ])
    confirmations.value = confirmationData.items
    partnerSplits.value = splitData.items
    milestones.value = milestoneData.items
    shipmentPlans.value = shipmentData.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '订单加载失败'
  } finally {
    loading.value = false
  }
}

async function onEnsureMilestones(split: PartnerSplit) {
  if (!order.value) return
  actionLoading.value = true
  error.value = ''
  try {
    await ensureProductionMilestones(order.value.id, split.id)
    const data = await fetchProductionMilestones(order.value.id)
    milestones.value = data.items
    successMsg.value = '生产节点已生成。'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '生成生产节点失败'
  } finally {
    actionLoading.value = false
  }
}

async function onMilestoneStatusChange(item: ProductionMilestone, status: string) {
  if (!order.value || item.status === status) return
  actionLoading.value = true
  error.value = ''
  try {
    await updateProductionMilestone(order.value.id, item.id, { status })
    const data = await fetchProductionMilestones(order.value.id)
    milestones.value = data.items
    successMsg.value = '生产节点状态已更新。'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '更新生产节点失败'
  } finally {
    actionLoading.value = false
  }
}

async function onShipmentStatusChange(plan: ShipmentPlan, status: string) {
  if (!order.value || plan.status === status) return
  actionLoading.value = true
  error.value = ''
  try {
    await updateShipmentPlan(order.value.id, plan.id, { status })
    const data = await fetchShipmentPlans(order.value.id)
    shipmentPlans.value = data.items
    successMsg.value = '物流状态已更新。'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '更新物流状态失败'
  } finally {
    actionLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="order-page">
    <button class="back-button" type="button" @click="router.push({ name: 'orders' })">返回订单列表</button>

    <div v-if="loading" v-loading="true" class="loading-panel" />

    <template v-else-if="order">
      <header class="order-hero">
        <div>
          <p class="eyebrow">订单执行</p>
          <h1>{{ order.order_number }}</h1>
          <p class="hero-copy">{{ order.bill_to_company || '未填写客户公司' }} · {{ executionStage }}</p>
        </div>
        <div class="hero-metrics">
          <div>
            <span>状态</span>
            <strong>{{ label(ORDER_STATUS, order.status) }}</strong>
          </div>
          <div>
            <span>金额</span>
            <strong>{{ formatMoney(order.grand_total, order.currency) }}</strong>
          </div>
          <div>
            <span>报价来源</span>
            <router-link v-if="order.source_quote" :to="{ name: 'quote-detail', params: { id: order.source_quote.quote_id } }">
              {{ order.source_quote.quote_number }}
            </router-link>
            <strong v-else>-</strong>
          </div>
        </div>
      </header>

      <el-alert v-if="error" type="error" :title="error" show-icon class="mb" @close="error = ''" />
      <el-alert v-if="successMsg" type="success" :title="successMsg" show-icon class="mb" @close="successMsg = ''" />

      <section class="compact-section safety-strip">
        <span>安全边界</span>
        <p>{{ safetyNote }}</p>
      </section>

      <section class="overview-grid">
        <article class="overview-card">
          <span>客户确认</span>
          <strong>{{ order.confirmation_summary?.active_count ?? confirmations.length }} 条有效确认</strong>
          <p>{{ confirmations[0]?.confirmation_type || '暂无确认方式' }}</p>
        </article>
        <article class="overview-card">
          <span>Partner 承接</span>
          <strong>{{ partnerSplits.length }} 个分单</strong>
          <p>{{ partnerSplits.map((item) => item.partner_name).join(' / ') || '暂无 Partner 分单' }}</p>
        </article>
        <article class="overview-card">
          <span>生产进度</span>
          <strong>{{ completedMilestoneCount }} / {{ visibleMilestones.length }}</strong>
          <p>{{ currentMilestone ? milestoneName(currentMilestone) : '暂无生产节点' }}</p>
        </article>
        <article class="overview-card">
          <span>物流计划</span>
          <strong>{{ activeShipment ? label(SHIPMENT_STATUS, activeShipment.status) : '暂无物流' }}</strong>
          <p>{{ activeShipment?.tracking_number || activeShipment?.destination || '未维护 tracking' }}</p>
        </article>
      </section>

      <section class="compact-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">Order Items</p>
            <h2>订单产品</h2>
          </div>
        </div>
        <el-table :data="order.line_items" stripe>
          <el-table-column prop="product_name" label="产品" min-width="260" />
          <el-table-column prop="quantity" label="数量" width="90" />
          <el-table-column label="单价" width="140">
            <template #default="{ row }">{{ formatMoney(row.unit_price, row.currency) }}</template>
          </el-table-column>
          <el-table-column label="合计" width="140">
            <template #default="{ row }">{{ formatMoney(row.total_price, row.currency) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">{{ label(ORDER_STATUS, row.status) }}</template>
          </el-table-column>
        </el-table>
      </section>

      <section class="compact-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">Production Flow</p>
            <h2>生产节点</h2>
          </div>
          <el-button
            v-if="!visibleMilestones.length && partnerSplits[0]"
            type="primary"
            :loading="actionLoading"
            @click="onEnsureMilestones(partnerSplits[0])"
          >
            生成标准节点
          </el-button>
        </div>

        <div v-if="visibleMilestones.length" class="production-flow">
          <article
            v-for="item in visibleMilestones"
            :key="item.id"
            class="flow-node"
            :class="statusClass(item.status)"
          >
            <div class="node-index">{{ item.sequence }}</div>
            <div class="node-body">
              <strong>{{ milestoneName(item) }}</strong>
              <p>计划 {{ formatDate(item.planned_date) }} · 实际 {{ formatDate(item.actual_date) }}</p>
              <p v-if="item.notes" class="node-note">{{ item.notes }}</p>
            </div>
            <el-select
              :model-value="item.status"
              size="small"
              class="node-select"
              :disabled="actionLoading"
              @change="(status: string) => onMilestoneStatusChange(item, status)"
            >
              <el-option label="待开始" value="planned" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已完成" value="completed" />
              <el-option label="延误" value="delayed" />
              <el-option label="阻塞" value="blocked" />
            </el-select>
          </article>
        </div>
        <el-empty v-else description="暂无生产节点" />
      </section>

      <section class="compact-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">Shipment</p>
            <h2>物流节点</h2>
          </div>
        </div>
        <div v-if="shipmentPlans.length" class="shipment-list">
          <article v-for="plan in shipmentPlans" :key="plan.id" class="shipment-card">
            <div>
              <strong>{{ plan.shipment_method || '物流计划' }} · {{ plan.incoterm || '未设置条款' }}</strong>
              <p>{{ plan.origin || '未设置起运地' }} → {{ plan.destination || '未设置目的地' }}</p>
              <p>ETD {{ formatDate(plan.estimated_ship_date) }} · ETA {{ formatDate(plan.estimated_arrival_date) }}</p>
              <p v-if="plan.tracking_number">Tracking: {{ plan.tracking_number }}</p>
            </div>
            <el-select
              :model-value="plan.status"
              size="small"
              class="shipment-select"
              :disabled="actionLoading"
              @change="(status: string) => onShipmentStatusChange(plan, status)"
            >
              <el-option label="草稿" value="draft" />
              <el-option label="已计划" value="planned" />
              <el-option label="已订舱" value="booked" />
              <el-option label="运输中" value="in_transit" />
              <el-option label="已发运" value="shipped" />
              <el-option label="已交付" value="delivered" />
              <el-option label="延误" value="delayed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </article>
        </div>
        <el-empty v-else description="暂无物流计划" />
      </section>

      <section class="compact-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">Partner</p>
            <h2>Partner 承接</h2>
          </div>
        </div>
        <el-table :data="partnerSplits" stripe>
          <el-table-column prop="partner_name" label="Partner" min-width="160" />
          <el-table-column prop="split_number" label="分单号" min-width="180" />
          <el-table-column label="分单状态" width="140">
            <template #default="{ row }">{{ label(SUPPLIER_STATUS, row.split_status) }}</template>
          </el-table-column>
          <el-table-column label="供应商确认" width="140">
            <template #default="{ row }">{{ label(SUPPLIER_STATUS, row.supplier_confirmation_status) }}</template>
          </el-table-column>
          <el-table-column prop="expected_ready_date" label="预计完成" width="130" />
          <el-table-column label="金额" width="140">
            <template #default="{ row }">{{ formatMoney(row.subtotal, row.currency) }}</template>
          </el-table-column>
        </el-table>
      </section>
    </template>

    <el-empty v-else description="订单不存在" />
  </div>
</template>

<style scoped>
.order-page {
  min-height: 100vh;
  padding: 24px;
  background: #f5f7fb;
  color: #102033;
}

.back-button {
  border: 0;
  background: transparent;
  color: #2563eb;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 16px;
}

.loading-panel {
  min-height: 240px;
}

.order-hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px;
  border: 1px solid #dbe4f0;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffffff 0%, #eef5ff 100%);
  box-shadow: 0 12px 34px rgba(15, 35, 70, 0.08);
  margin-bottom: 18px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #3b82f6;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1,
h2 {
  margin: 0;
}

h1 {
  font-size: 34px;
  letter-spacing: 0;
}

h2 {
  font-size: 20px;
}

.hero-copy {
  margin: 10px 0 0;
  color: #62748d;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(120px, 1fr));
  gap: 12px;
  min-width: 460px;
}

.hero-metrics > div,
.overview-card,
.compact-section {
  border: 1px solid #dbe4f0;
  border-radius: 12px;
  background: #ffffff;
}

.hero-metrics > div {
  padding: 14px;
}

.hero-metrics span,
.overview-card span {
  display: block;
  color: #71839a;
  font-size: 13px;
  margin-bottom: 6px;
}

.hero-metrics strong,
.hero-metrics a,
.overview-card strong {
  color: #102033;
  font-size: 17px;
  font-weight: 700;
}

.mb {
  margin-bottom: 16px;
}

.safety-strip {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  margin-bottom: 16px;
  background: #f8fbff;
}

.safety-strip span {
  color: #2563eb;
  font-weight: 700;
}

.safety-strip p {
  margin: 0;
  color: #64748b;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.overview-card {
  padding: 18px;
}

.overview-card p {
  margin: 8px 0 0;
  color: #64748b;
}

.compact-section {
  padding: 20px;
  margin-bottom: 18px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.production-flow {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.flow-node {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) 132px;
  gap: 12px;
  align-items: center;
  border: 1px solid #dbe4f0;
  border-left: 4px solid #9aa9bb;
  border-radius: 10px;
  padding: 12px;
  background: #ffffff;
}

.flow-node.is-done {
  border-left-color: #16a34a;
  background: #f5fff8;
}

.flow-node.is-active {
  border-left-color: #2563eb;
  background: #f7fbff;
}

.flow-node.is-risk {
  border-left-color: #dc2626;
  background: #fff7f7;
}

.node-index {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #eaf2ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}

.node-body strong {
  display: block;
  margin-bottom: 4px;
}

.node-body p {
  margin: 0;
  color: #65758b;
  font-size: 13px;
}

.node-note {
  margin-top: 5px !important;
}

.node-select,
.shipment-select {
  width: 128px;
}

.shipment-list {
  display: grid;
  gap: 12px;
}

.shipment-card {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
  border: 1px solid #dbe4f0;
  border-radius: 12px;
  padding: 16px;
  background: #ffffff;
}

.shipment-card p {
  margin: 6px 0 0;
  color: #64748b;
}

@media (max-width: 1100px) {
  .order-hero {
    flex-direction: column;
  }

  .hero-metrics {
    min-width: 0;
    grid-template-columns: 1fr;
  }

  .overview-grid,
  .production-flow {
    grid-template-columns: 1fr;
  }
}
</style>
