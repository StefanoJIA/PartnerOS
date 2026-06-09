<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { UploadRequestOptions } from 'element-plus'
import { uploadFile } from '@/api/objects'
import { fetchFeedbackTickets, type FeedbackTicket } from '@/api/feedbackTickets'
import {
  addSupplierConfirmation,
  cancelOrder,
  confirmOrderCustomer,
  confirmationTypeWarning,
  createOrderResource,
  createShipmentPlan,
  ensurePartnerSplits,
  ensureProductionMilestones,
  fetchOrder,
  fetchOrderConfirmations,
  fetchOrderResources,
  fetchOrderTimeline,
  fetchPartnerSplits,
  fetchPartnerSplitDetail,
  fetchProductionMilestones,
  fetchShipmentPlans,
  updateOrderResource,
  updateProductionMilestone,
  updateShipmentPlan,
  strengthTagType,
  SUPPLIER_SAFETY_NOTE,
  PRODUCTION_SAFETY_NOTE,
  SHIPMENT_SAFETY_NOTE,
  voidOrderConfirmation,
  type OrderConfirmationRecord,
  type OrderDetail,
  type OrderResource,
  type OrderTimelineItem,
  type PartnerSplit,
  type ProductionMilestone,
  type ShipmentPlan,
} from '@/api/orders'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const order = ref<OrderDetail | null>(null)
const confirmations = ref<OrderConfirmationRecord[]>([])
const partnerSplits = ref<PartnerSplit[]>([])
const expandedSplitId = ref<string | null>(null)
const splitDetails = ref<Record<string, PartnerSplit>>({})
const timelineItems = ref<OrderTimelineItem[]>([])
const actionLoading = ref(false)
const successMsg = ref('')
const showAddForm = ref(false)
const showSupplierFormFor = ref<string | null>(null)
const milestonesBySplit = ref<Record<string, ProductionMilestone[]>>({})
const shipmentPlans = ref<ShipmentPlan[]>([])
const orderResources = ref<OrderResource[]>([])
const feedbackTickets = ref<FeedbackTicket[]>([])
const resourceUploading = ref(false)
const editingMilestoneId = ref<string | null>(null)
const milestoneForm = reactive({
  status: 'planned',
  planned_date: '',
  actual_date: '',
  responsible_party: '',
  notes: '',
})
const shipmentForm = reactive({
  partner_split_id: '',
  shipment_method: 'sea',
  incoterm: '',
  origin: '',
  destination: '',
  estimated_ship_date: '',
  estimated_arrival_date: '',
  tracking_number: '',
  status: 'draft',
  notes: '',
})
const resourceForm = reactive({
  title: '',
  category: 'general',
  description: '',
  customer_visible: false,
})

const SAFETY =
  '记录客户确认不会通知供应商、启动生产、创建物流、确认库存、确认认证或确认交期。'
const RESOURCE_SAFETY_NOTE =
  '订单资料是人工发布给客户的文件。发布只创建签名下载链接，不发送邮件、不暴露存储路径，也不会自动通知 Portal。'

const supplierForm = reactive({
  confirmation_status: 'confirmed',
  confirmed_by_name: '',
  confirmed_by_email: '',
  confirmation_channel: 'email',
  inventory_confirmed: false,
  certification_confirmed: false,
  lead_time_confirmed: false,
  production_capacity_confirmed: false,
  expected_production_start: '',
  expected_ready_date: '',
  supplier_reference: '',
  note: '',
})

const confirmForm = reactive({
  confirmation_type: 'email',
  confirmed_by_name: '',
  confirmed_by_email: '',
  confirmed_by_company: '',
  source_channel: '',
  evidence_reference: '',
  note: '',
})

const cancelReason = ref('')

const canAddConfirmation = computed(() => order.value?.status !== 'cancelled')
const canEnsureSplits = computed(() => order.value?.status !== 'cancelled')
const canAddSupplierConfirmation = computed(() => order.value?.status === 'confirmed')
const canEnsureMilestones = computed(() => order.value?.status === 'confirmed')
const canManageShipments = computed(() => {
  const allowed = [
    'confirmed',
    'internal_review',
    'supplier_confirmation_pending',
    'supplier_confirmed',
    'production_pending',
    'in_production',
    'ready_to_ship',
    'shipped',
    'delivered',
    'on_hold',
  ]
  return !!order.value && allowed.includes(order.value.status)
})
const canCancel = computed(() => order.value && ['pending_customer_confirmation', 'confirmed'].includes(order.value.status))
const typeWarning = computed(() => confirmationTypeWarning(confirmForm.confirmation_type))
const orderWarnings = computed(() => order.value?.warnings || order.value?.confirmation_summary?.warnings || [])
const openFeedbackTickets = computed(() => feedbackTickets.value.filter((ticket) => ticket.operation?.open))
const visibleResourceCount = computed(() => orderResources.value.filter((resource) => resource.customer_visible && resource.status === 'published').length)
const customerVisibleSummary = computed(() => {
  const production = order.value?.production_summary
  const shipment = order.value?.shipment_summary
  const totalMilestones = production?.total_milestones ?? 0
  const completedMilestones = production?.completed_milestones ?? 0
  const stage =
    shipment?.delivered_plans ? '已交付'
    : shipment?.shipped_plans ? '运输中'
    : production?.ready_to_ship_completed ? '待发运'
    : production?.in_progress_milestones ? '生产中'
    : order.value?.status === 'confirmed' ? '订单已确认'
    : '订单录入'
  const nextAction =
    shipment?.delivered_plans ? '收集反馈并关闭运营闭环。'
    : shipment?.shipped_plans ? '跟踪物流和客户收货反馈。'
    : production?.ready_to_ship_completed ? '确认物流计划和客户可见物流信息。'
    : production?.in_progress_milestones ? '复核生产里程碑和预计完成日期。'
    : order.value?.status === 'confirmed' ? '确认 partner 分单、供应商 readiness 和生产计划。'
    : '先记录客户确认，再规划生产或物流。'
  return {
    stage,
    nextAction,
    production: totalMilestones ? `${completedMilestones}/${totalMilestones} 个里程碑完成` : '暂无生产里程碑',
    shipment: shipment?.total_plans ? `${shipment.active_plans} 个进行中 / ${shipment.total_plans} 个物流计划` : '暂无物流计划',
    resources: `${visibleResourceCount.value} 个客户可见资料`,
    feedback: `${openFeedbackTickets.value.length} 个未结反馈`,
  }
})

async function loadPartnerSplits() {
  if (!order.value) return
  const ps = await fetchPartnerSplits(order.value.id)
  partnerSplits.value = ps.items
}

async function loadShipmentPlans() {
  if (!order.value) return
  const plans = await fetchShipmentPlans(order.value.id)
  shipmentPlans.value = plans.items
}

async function loadOrderResources() {
  if (!order.value) return
  const resources = await fetchOrderResources(order.value.id)
  orderResources.value = resources.items
}

async function loadFeedbackTickets() {
  if (!order.value) return
  const tickets = await fetchFeedbackTickets({ order_id: order.value.id, limit: 20 })
  feedbackTickets.value = tickets.items
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const id = route.params.orderId as string
    order.value = await fetchOrder(id)
    const conf = await fetchOrderConfirmations(id)
    confirmations.value = conf.items
    await loadPartnerSplits()
    await loadShipmentPlans()
    await loadOrderResources()
    await loadFeedbackTickets()
    const tl = await fetchOrderTimeline(id)
    timelineItems.value = tl.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '订单加载失败'
  } finally {
    loading.value = false
  }
}

async function onUploadOrderResource(opt: UploadRequestOptions) {
  if (!order.value) return
  resourceUploading.value = true
  error.value = ''
  try {
    const raw = opt.file as File
    const meta = await uploadFile(raw)
    await createOrderResource(order.value.id, {
      file_id: meta.id,
      title: resourceForm.title || meta.original_filename,
      category: resourceForm.category,
      description: resourceForm.description || undefined,
      customer_visible: resourceForm.customer_visible,
    })
    resourceForm.title = ''
    resourceForm.description = ''
    resourceForm.customer_visible = false
    await loadOrderResources()
    const tl = await fetchOrderTimeline(order.value.id)
    timelineItems.value = tl.items
    successMsg.value = 'Order resource created.'
    opt.onSuccess?.({} as never)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Upload order resource failed'
    const uploadError = Object.assign(e instanceof Error ? e : new Error('Upload order resource failed'), {
      status: 0,
      method: 'POST',
      url: '',
    }) as Parameters<NonNullable<UploadRequestOptions['onError']>>[0]
    opt.onError?.(uploadError)
  } finally {
    resourceUploading.value = false
  }
}

async function onPatchOrderResource(resource: OrderResource, patch: Partial<OrderResource>) {
  if (!order.value) return
  actionLoading.value = true
  error.value = ''
  try {
    await updateOrderResource(order.value.id, resource.id, {
      title: patch.title,
      category: patch.category,
      description: patch.description ?? undefined,
      status: patch.status,
      customer_visible: patch.customer_visible,
    })
    await loadOrderResources()
    successMsg.value = 'Order resource updated.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Update order resource failed'
  } finally {
    actionLoading.value = false
  }
}

async function onCreateShipmentPlan() {
  if (!order.value) return
  actionLoading.value = true
  error.value = ''
  try {
    await createShipmentPlan(order.value.id, {
      partner_split_id: shipmentForm.partner_split_id || undefined,
      shipment_method: shipmentForm.shipment_method || undefined,
      incoterm: shipmentForm.incoterm || undefined,
      origin: shipmentForm.origin || undefined,
      destination: shipmentForm.destination || undefined,
      estimated_ship_date: shipmentForm.estimated_ship_date || undefined,
      estimated_arrival_date: shipmentForm.estimated_arrival_date || undefined,
      tracking_number: shipmentForm.tracking_number || undefined,
      status: shipmentForm.status,
      notes: shipmentForm.notes || undefined,
    })
    await loadShipmentPlans()
    order.value = await fetchOrder(order.value.id)
    const tl = await fetchOrderTimeline(order.value.id)
    timelineItems.value = tl.items
    successMsg.value = 'Shipment plan created.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Create shipment plan failed'
  } finally {
    actionLoading.value = false
  }
}

async function onPatchShipmentStatus(plan: ShipmentPlan, status: string) {
  if (!order.value) return
  actionLoading.value = true
  error.value = ''
  try {
    await updateShipmentPlan(order.value.id, plan.id, { status })
    await loadShipmentPlans()
    order.value = await fetchOrder(order.value.id)
    const tl = await fetchOrderTimeline(order.value.id)
    timelineItems.value = tl.items
    successMsg.value = status === 'cancelled' ? 'Shipment plan cancelled.' : 'Shipment status updated.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Update shipment plan failed'
  } finally {
    actionLoading.value = false
  }
}

async function onEnsureSplits() {
  if (!order.value) return
  actionLoading.value = true
  error.value = ''
  try {
    const result = await ensurePartnerSplits(order.value.id)
    order.value = result
    partnerSplits.value = result.splits || (await fetchPartnerSplits(order.value.id)).items
    successMsg.value = 'Partner splits ensured.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ensure splits failed'
  } finally {
    actionLoading.value = false
  }
}

async function toggleSplitDetail(split: PartnerSplit) {
  if (expandedSplitId.value === split.id) {
    expandedSplitId.value = null
    return
  }
  expandedSplitId.value = split.id
  if (!order.value) return
  if (!splitDetails.value[split.id]) {
    splitDetails.value[split.id] = await fetchPartnerSplitDetail(order.value.id, split.id)
  }
  await loadMilestonesForSplit(split.id)
}

async function loadMilestonesForSplit(splitId: string) {
  if (!order.value) return
  const ms = await fetchProductionMilestones(order.value.id, splitId)
  milestonesBySplit.value[splitId] = ms.items
}

async function onEnsureMilestones(splitId: string) {
  if (!order.value) return
  actionLoading.value = true
  error.value = ''
  try {
    order.value = await ensureProductionMilestones(order.value.id, splitId)
    await loadMilestonesForSplit(splitId)
    await loadPartnerSplits()
    successMsg.value = 'Production milestones ensured.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Ensure milestones failed'
  } finally {
    actionLoading.value = false
  }
}

function startEditMilestone(m: ProductionMilestone) {
  editingMilestoneId.value = m.id
  milestoneForm.status = m.status
  milestoneForm.planned_date = m.planned_date || ''
  milestoneForm.actual_date = m.actual_date || ''
  milestoneForm.responsible_party = m.responsible_party || ''
  milestoneForm.notes = m.notes || ''
}

async function onUpdateMilestone(m: ProductionMilestone) {
  if (!order.value) return
  actionLoading.value = true
  error.value = ''
  try {
    await updateProductionMilestone(order.value.id, m.id, {
      status: milestoneForm.status,
      planned_date: milestoneForm.planned_date || undefined,
      actual_date: milestoneForm.actual_date || undefined,
      responsible_party: milestoneForm.responsible_party || undefined,
      notes: milestoneForm.notes || undefined,
    })
    await loadMilestonesForSplit(m.partner_split_id)
    order.value = await fetchOrder(order.value.id)
    const tl = await fetchOrderTimeline(order.value.id)
    timelineItems.value = tl.items
    editingMilestoneId.value = null
    successMsg.value = 'Milestone updated.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Update milestone failed'
  } finally {
    actionLoading.value = false
  }
}

async function onAddSupplierConfirmation(splitId: string) {
  if (!order.value) return
  actionLoading.value = true
  error.value = ''
  try {
    const result = await addSupplierConfirmation(order.value.id, splitId, {
      confirmation_status: supplierForm.confirmation_status,
      confirmed_by_name: supplierForm.confirmed_by_name || undefined,
      confirmed_by_email: supplierForm.confirmed_by_email || undefined,
      confirmation_channel: supplierForm.confirmation_channel || undefined,
      inventory_confirmed: supplierForm.inventory_confirmed,
      certification_confirmed: supplierForm.certification_confirmed,
      lead_time_confirmed: supplierForm.lead_time_confirmed,
      production_capacity_confirmed: supplierForm.production_capacity_confirmed,
      expected_production_start: supplierForm.expected_production_start || undefined,
      expected_ready_date: supplierForm.expected_ready_date || undefined,
      supplier_reference: supplierForm.supplier_reference || undefined,
      note: supplierForm.note || undefined,
    })
    splitDetails.value[splitId] = result
    await loadPartnerSplits()
    order.value = await fetchOrder(order.value.id)
    const tl = await fetchOrderTimeline(order.value.id)
    timelineItems.value = tl.items
    showSupplierFormFor.value = null
    successMsg.value = 'Supplier confirmation recorded.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Supplier confirmation failed'
  } finally {
    actionLoading.value = false
  }
}

async function onConfirm() {
  if (!order.value) return
  actionLoading.value = true
  successMsg.value = ''
  error.value = ''
  try {
    const result = await confirmOrderCustomer(order.value.id, {
      confirmation_type: confirmForm.confirmation_type,
      confirmed_by_name: confirmForm.confirmed_by_name || undefined,
      confirmed_by_email: confirmForm.confirmed_by_email || undefined,
      confirmed_by_company: confirmForm.confirmed_by_company || undefined,
      source_channel: confirmForm.source_channel || undefined,
      evidence_reference: confirmForm.evidence_reference || undefined,
      note: confirmForm.note || undefined,
    })
    order.value = result
    const conf = await fetchOrderConfirmations(order.value.id)
    confirmations.value = conf.items
    const tl = await fetchOrderTimeline(order.value.id)
    timelineItems.value = tl.items
    showAddForm.value = false
    successMsg.value = result.status_changed ? 'Order confirmed.' : 'Confirmation recorded.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Confirm failed'
  } finally {
    actionLoading.value = false
  }
}

async function onVoid(conf: OrderConfirmationRecord) {
  if (!order.value || conf.status !== 'active') return
  actionLoading.value = true
  error.value = ''
  try {
    order.value = await voidOrderConfirmation(order.value.id, conf.id, 'Voided from order detail')
    const list = await fetchOrderConfirmations(order.value.id)
    confirmations.value = list.items
    const tl = await fetchOrderTimeline(order.value.id)
    timelineItems.value = tl.items
    successMsg.value = 'Confirmation voided.'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Void failed'
  } finally {
    actionLoading.value = false
  }
}

async function onCancel() {
  if (!order.value) return
  actionLoading.value = true
  successMsg.value = ''
  try {
    order.value = await cancelOrder(order.value.id, cancelReason.value || undefined)
    successMsg.value = 'Order cancelled.'
    const tl = await fetchOrderTimeline(order.value.id)
    timelineItems.value = tl.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Cancel failed'
  } finally {
    actionLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <el-button link type="primary" @click="router.push({ name: 'orders' })">← 返回订单</el-button>

    <div v-if="loading" v-loading="true" style="min-height: 160px" />
    <template v-else-if="order">
      <h1>{{ order.order_number }}</h1>
      <el-alert type="warning" :closable="false" show-icon title="确认安全边界" :description="SAFETY" class="mb" />
      <el-alert v-if="error" type="error" :title="error" show-icon class="mb" @close="error = ''" />
      <el-alert v-if="successMsg" type="success" :title="successMsg" show-icon class="mb" @close="successMsg = ''" />
      <el-alert
        v-for="(w, i) in orderWarnings"
        :key="i"
        type="warning"
        :title="w"
        show-icon
        class="mb"
      />

      <el-descriptions :column="2" border class="mb">
        <el-descriptions-item label="状态">{{ order.status }}</el-descriptions-item>
        <el-descriptions-item label="有效确认">{{ order.confirmation_summary?.active_count ?? 0 }}</el-descriptions-item>
        <el-descriptions-item label="总金额">{{ order.currency }} {{ order.grand_total }}</el-descriptions-item>
        <el-descriptions-item label="来源报价">
          <router-link
            v-if="order.source_quote"
            class="link"
            :to="{ name: 'quote-detail', params: { id: order.source_quote.quote_id } }"
          >
            {{ order.source_quote.quote_number }}
          </router-link>
          <span v-else>—</span>
        </el-descriptions-item>
      </el-descriptions>

      <section class="section mb">
        <div class="section-head">
          <h3>客户可见运营摘要</h3>
          <div class="flex gap-2">
            <el-button size="small" @click="router.push({ name: 'portal-customer-bridge', query: { order_id: order.id } })">
              Portal 预览
            </el-button>
            <el-button size="small" @click="router.push({ name: 'feedback-tickets', query: { order_id: order.id } })">
              反馈队列
            </el-button>
          </div>
        </div>
        <el-alert
          type="info"
          :closable="false"
          class="mb"
          title="客户可见摘要只使用白名单内的生产、物流、资料和反馈元数据。"
        />
        <div class="customer-stage mb">
          <div>
            <div class="summary-label">当前客户可见阶段</div>
            <div class="customer-stage-title">{{ customerVisibleSummary.stage }}</div>
            <p class="customer-stage-copy">{{ customerVisibleSummary.nextAction }}</p>
          </div>
          <el-tag effect="plain">Portal 安全</el-tag>
        </div>
        <div class="summary-grid">
          <div class="summary-tile">
            <div class="summary-label">生产</div>
            <div class="summary-value">{{ customerVisibleSummary.production }}</div>
          </div>
          <div class="summary-tile">
            <div class="summary-label">物流</div>
            <div class="summary-value">{{ customerVisibleSummary.shipment }}</div>
          </div>
          <div class="summary-tile">
            <div class="summary-label">资料</div>
            <div class="summary-value">{{ customerVisibleSummary.resources }}</div>
          </div>
          <div class="summary-tile">
            <div class="summary-label">反馈</div>
            <div class="summary-value">{{ customerVisibleSummary.feedback }}</div>
          </div>
        </div>
      </section>

      <section class="section mb">
        <h3>订单行</h3>
        <el-table :data="order.line_items" stripe>
          <el-table-column prop="product_name" label="产品" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="unit_price" label="单价" width="120" />
          <el-table-column prop="total_price" label="合计" width="120" />
          <el-table-column prop="status" label="状态" width="120" />
        </el-table>
      </section>

      <section class="section mb">
        <div class="section-head">
          <h3>客户确认</h3>
          <el-button v-if="canAddConfirmation" type="primary" @click="showAddForm = !showAddForm">
            添加确认
          </el-button>
        </div>

        <el-table :data="confirmations" stripe class="mb">
          <el-table-column prop="confirmation_type" label="类型" width="140" />
          <el-table-column label="强度" width="100">
            <template #default="{ row }">
              <el-tag :type="strengthTagType(row.confirmation_strength)" size="small">{{ row.confirmation_strength }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="confirmed_at" label="确认时间" width="180" />
          <el-table-column prop="confirmed_by_name" label="确认人" width="120" />
          <el-table-column prop="evidence_reference" label="证据" />
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column label="" width="100">
            <template #default="{ row }">
              <el-button v-if="row.status === 'active'" size="small" @click="onVoid(row)">作废</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-form v-if="showAddForm && canAddConfirmation" label-width="160px" @submit.prevent="onConfirm">
          <el-form-item label="Type">
            <el-select v-model="confirmForm.confirmation_type" style="width: 220px">
              <el-option label="Email" value="email" />
              <el-option label="Purchase Order" value="purchase_order" />
              <el-option label="Signed Quote" value="signed_quote" />
              <el-option label="Verbal" value="verbal" />
              <el-option label="Internal Note" value="internal_note" />
              <el-option label="Other" value="other" />
            </el-select>
          </el-form-item>
          <el-alert v-if="typeWarning" type="warning" :title="typeWarning" show-icon class="mb" />
          <el-form-item label="Confirmed By">
            <el-input v-model="confirmForm.confirmed_by_name" />
          </el-form-item>
          <el-form-item label="Email">
            <el-input v-model="confirmForm.confirmed_by_email" />
          </el-form-item>
          <el-form-item label="Company">
            <el-input v-model="confirmForm.confirmed_by_company" />
          </el-form-item>
          <el-form-item label="Evidence Reference">
            <el-input v-model="confirmForm.evidence_reference" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="Note">
            <el-input v-model="confirmForm.note" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="actionLoading" @click="onConfirm">Record Confirmation</el-button>
          </el-form-item>
        </el-form>
      </section>

      <section class="section mb">
        <div class="section-head">
          <h3>Partner Splits</h3>
          <el-button v-if="canEnsureSplits" type="primary" :loading="actionLoading" @click="onEnsureSplits">
            Ensure Partner Splits
          </el-button>
        </div>
        <el-alert type="warning" :closable="false" show-icon title="Supplier Safety" :description="SUPPLIER_SAFETY_NOTE" class="mb" />
        <el-alert
          v-if="order.status === 'pending_customer_confirmation'"
          type="warning"
          title="Customer confirmation is not recorded; supplier actions should be reviewed."
          show-icon
          class="mb"
        />
        <el-descriptions v-if="order.partner_splits_summary" :column="4" border class="mb">
          <el-descriptions-item label="Total Splits">{{ order.partner_splits_summary.total_splits }}</el-descriptions-item>
          <el-descriptions-item label="Confirmed">{{ order.partner_splits_summary.confirmed_splits }}</el-descriptions-item>
          <el-descriptions-item label="Pending">{{ order.partner_splits_summary.pending_splits }}</el-descriptions-item>
          <el-descriptions-item label="Needs Clarification">{{ order.partner_splits_summary.needs_clarification_splits }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="partnerSplits" stripe class="mb">
          <el-table-column prop="split_number" label="Split" width="100" />
          <el-table-column prop="partner_name" label="Partner" width="160" />
          <el-table-column prop="split_status" label="Split Status" width="180" />
          <el-table-column prop="supplier_confirmation_status" label="Supplier Conf." width="140" />
          <el-table-column prop="line_item_count" label="Lines" width="80" />
          <el-table-column label="Subtotal" width="120">
            <template #default="{ row }">{{ row.currency }} {{ row.subtotal }}</template>
          </el-table-column>
          <el-table-column prop="expected_ready_date" label="Expected Ready" width="120" />
          <el-table-column label="" width="120">
            <template #default="{ row }">
              <el-button size="small" @click="toggleSplitDetail(row)">Details</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-for="split in partnerSplits" :key="split.id">
          <div v-if="expandedSplitId === split.id" class="split-detail mb">
            <h4>{{ split.partner_name }} — {{ split.split_number }}</h4>
            <el-table :data="(splitDetails[split.id]?.line_items || [])" stripe size="small" class="mb">
              <el-table-column prop="product_name" label="Product" />
              <el-table-column prop="quantity" label="Qty" width="80" />
              <el-table-column prop="total_price" label="Total" width="100" />
            </el-table>
            <h5>Supplier Confirmations</h5>
            <el-table :data="splitDetails[split.id]?.supplier_confirmations || []" stripe size="small" class="mb">
              <el-table-column prop="confirmation_status" label="Status" width="120" />
              <el-table-column prop="confirmed_at" label="Confirmed At" width="160" />
              <el-table-column prop="confirmed_by_name" label="By" width="120" />
              <el-table-column label="Flags" width="200">
                <template #default="{ row }">
                  <el-tag v-if="row.inventory_confirmed" size="small" type="success">Inventory</el-tag>
                  <el-tag v-if="row.lead_time_confirmed" size="small" type="success">Lead Time</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="Record" width="90" />
            </el-table>
            <el-button
              v-if="canAddSupplierConfirmation"
              size="small"
              @click="showSupplierFormFor = showSupplierFormFor === split.id ? null : split.id"
            >
              Add Supplier Confirmation
            </el-button>
            <el-form
              v-if="showSupplierFormFor === split.id && canAddSupplierConfirmation"
              label-width="200px"
              class="mt"
              @submit.prevent="onAddSupplierConfirmation(split.id)"
            >
              <el-form-item label="Status">
                <el-select v-model="supplierForm.confirmation_status" style="width: 220px">
                  <el-option label="Confirmed" value="confirmed" />
                  <el-option label="Partially Confirmed" value="partially_confirmed" />
                  <el-option label="Needs Clarification" value="needs_clarification" />
                  <el-option label="Rejected" value="rejected" />
                </el-select>
              </el-form-item>
              <el-form-item label="Confirmed By"><el-input v-model="supplierForm.confirmed_by_name" /></el-form-item>
              <el-form-item label="Email"><el-input v-model="supplierForm.confirmed_by_email" /></el-form-item>
              <el-form-item label="Channel"><el-input v-model="supplierForm.confirmation_channel" /></el-form-item>
              <el-form-item label="Inventory Confirmed"><el-checkbox v-model="supplierForm.inventory_confirmed" /></el-form-item>
              <el-form-item label="Certification Confirmed"><el-checkbox v-model="supplierForm.certification_confirmed" /></el-form-item>
              <el-form-item label="Lead Time Confirmed"><el-checkbox v-model="supplierForm.lead_time_confirmed" /></el-form-item>
              <el-form-item label="Production Capacity"><el-checkbox v-model="supplierForm.production_capacity_confirmed" /></el-form-item>
              <el-form-item label="Expected Production Start"><el-input v-model="supplierForm.expected_production_start" placeholder="YYYY-MM-DD" /></el-form-item>
              <el-form-item label="Expected Ready Date"><el-input v-model="supplierForm.expected_ready_date" placeholder="YYYY-MM-DD" /></el-form-item>
              <el-form-item label="Supplier Reference"><el-input v-model="supplierForm.supplier_reference" /></el-form-item>
              <el-form-item label="Note"><el-input v-model="supplierForm.note" type="textarea" :rows="2" /></el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="actionLoading" @click="onAddSupplierConfirmation(split.id)">Record</el-button>
              </el-form-item>
            </el-form>
            <h5 class="mt">Production Milestones</h5>
            <el-alert type="info" :closable="false" :description="PRODUCTION_SAFETY_NOTE" class="mb" />
            <el-button
              v-if="canEnsureMilestones"
              size="small"
              class="mb"
              :loading="actionLoading"
              @click="onEnsureMilestones(split.id)"
            >
              Ensure Milestones
            </el-button>
            <el-table :data="milestonesBySplit[split.id] || []" stripe size="small" class="mb">
              <el-table-column prop="sequence" label="#" width="50" />
              <el-table-column prop="milestone_label" label="Milestone" />
              <el-table-column prop="status" label="Status" width="110" />
              <el-table-column prop="planned_date" label="Planned" width="110" />
              <el-table-column prop="actual_date" label="Actual" width="110" />
              <el-table-column label="" width="90">
                <template #default="{ row }">
                  <el-button v-if="canEnsureMilestones" size="small" @click="startEditMilestone(row)">Update</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-form
              v-if="editingMilestoneId && (milestonesBySplit[split.id] || []).some(m => m.id === editingMilestoneId)"
              label-width="140px"
              class="mt"
            >
              <el-form-item label="Status">
                <el-select v-model="milestoneForm.status" style="width: 200px">
                  <el-option label="Planned" value="planned" />
                  <el-option label="In Progress" value="in_progress" />
                  <el-option label="Completed" value="completed" />
                  <el-option label="Delayed" value="delayed" />
                  <el-option label="Blocked" value="blocked" />
                </el-select>
              </el-form-item>
              <el-form-item label="Planned Date"><el-input v-model="milestoneForm.planned_date" placeholder="YYYY-MM-DD" /></el-form-item>
              <el-form-item label="Actual Date"><el-input v-model="milestoneForm.actual_date" placeholder="YYYY-MM-DD" /></el-form-item>
              <el-form-item label="Responsible"><el-input v-model="milestoneForm.responsible_party" /></el-form-item>
              <el-form-item label="Notes"><el-input v-model="milestoneForm.notes" type="textarea" :rows="2" /></el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="actionLoading"
                  @click="onUpdateMilestone((milestonesBySplit[split.id] || []).find(m => m.id === editingMilestoneId)!)"
                >
                  Save Milestone
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </section>

      <section v-if="order.production_summary" class="section mb">
        <h3>Production Summary</h3>
        <el-descriptions :column="4" border>
          <el-descriptions-item label="Total">{{ order.production_summary.total_milestones }}</el-descriptions-item>
          <el-descriptions-item label="Completed">{{ order.production_summary.completed_milestones }}</el-descriptions-item>
          <el-descriptions-item label="In Progress">{{ order.production_summary.in_progress_milestones }}</el-descriptions-item>
          <el-descriptions-item label="Shipment Created">{{ order.production_summary.shipment_created ? 'Yes' : 'No' }}</el-descriptions-item>
        </el-descriptions>
      </section>

      <section class="section mb">
        <div class="section-head">
          <h3>Shipment Plans</h3>
          <el-tag type="info">Manual</el-tag>
        </div>
        <el-alert type="info" :closable="false" :description="SHIPMENT_SAFETY_NOTE" class="mb" />
        <el-table :data="shipmentPlans" stripe class="mb">
          <el-table-column prop="status" label="Status" width="110" />
          <el-table-column prop="shipment_method" label="Method" width="110" />
          <el-table-column prop="origin" label="Origin" />
          <el-table-column prop="destination" label="Destination" />
          <el-table-column prop="estimated_ship_date" label="ETD" width="120" />
          <el-table-column prop="estimated_arrival_date" label="ETA" width="120" />
          <el-table-column prop="tracking_number" label="Tracking" width="140" />
          <el-table-column label="" width="180">
            <template #default="{ row }">
              <el-select
                :model-value="row.status"
                size="small"
                style="width: 150px"
                :disabled="!canManageShipments || actionLoading"
                @change="(status: string) => onPatchShipmentStatus(row, status)"
              >
                <el-option label="Draft" value="draft" />
                <el-option label="Planned" value="planned" />
                <el-option label="Shipped" value="shipped" />
                <el-option label="Delivered" value="delivered" />
                <el-option label="Cancelled" value="cancelled" />
              </el-select>
            </template>
          </el-table-column>
        </el-table>
        <el-collapse v-if="shipmentPlans.length" class="mb">
          <el-collapse-item title="Customer visible summary preview" name="shipment-summary">
            <el-table :data="shipmentPlans.map(p => p.portal_visible_fields || p)" stripe size="small">
              <el-table-column prop="status" label="Status" width="110" />
              <el-table-column prop="shipment_method" label="Method" width="110" />
              <el-table-column prop="estimated_ship_date" label="ETD" width="120" />
              <el-table-column prop="estimated_arrival_date" label="ETA" width="120" />
              <el-table-column prop="tracking_number" label="Tracking" />
            </el-table>
          </el-collapse-item>
        </el-collapse>
        <el-alert
          v-if="!canManageShipments"
          type="warning"
          title="Shipment plans require a customer-confirmed order."
          show-icon
          class="mb"
        />
        <el-form v-else label-width="150px" class="shipment-form" @submit.prevent="onCreateShipmentPlan">
          <el-form-item label="Partner Split">
            <el-select v-model="shipmentForm.partner_split_id" clearable placeholder="Optional" style="width: 260px">
              <el-option
                v-for="split in partnerSplits"
                :key="split.id"
                :label="`${split.split_number} - ${split.partner_name}`"
                :value="split.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="Method">
            <el-select v-model="shipmentForm.shipment_method" style="width: 180px">
              <el-option label="Sea" value="sea" />
              <el-option label="Air" value="air" />
              <el-option label="Express" value="express" />
            </el-select>
          </el-form-item>
          <el-form-item label="Status">
            <el-select v-model="shipmentForm.status" style="width: 180px">
              <el-option label="Draft" value="draft" />
              <el-option label="Planned" value="planned" />
            </el-select>
          </el-form-item>
          <el-form-item label="Incoterm"><el-input v-model="shipmentForm.incoterm" /></el-form-item>
          <el-form-item label="Origin"><el-input v-model="shipmentForm.origin" /></el-form-item>
          <el-form-item label="Destination"><el-input v-model="shipmentForm.destination" /></el-form-item>
          <el-form-item label="ETD"><el-input v-model="shipmentForm.estimated_ship_date" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="ETA"><el-input v-model="shipmentForm.estimated_arrival_date" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="Tracking"><el-input v-model="shipmentForm.tracking_number" /></el-form-item>
          <el-form-item label="Notes"><el-input v-model="shipmentForm.notes" type="textarea" :rows="2" /></el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="actionLoading" @click="onCreateShipmentPlan">Create Plan</el-button>
          </el-form-item>
        </el-form>
      </section>

      <section class="section mb">
        <div class="section-head">
          <h3>Resource Center</h3>
          <el-tag type="info">Manual publish</el-tag>
        </div>
        <el-alert type="info" :closable="false" :description="RESOURCE_SAFETY_NOTE" class="mb" />
        <el-table :data="orderResources" stripe class="mb">
          <el-table-column prop="title" label="Title" min-width="180" />
          <el-table-column prop="filename" label="File" min-width="180" />
          <el-table-column prop="category" label="Category" width="130" />
          <el-table-column prop="status" label="Status" width="110">
            <template #default="{ row }">
              <el-tag :type="row.status === 'published' ? 'success' : row.status === 'archived' ? 'info' : 'warning'" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Customer" width="120">
            <template #default="{ row }">
              <el-tag :type="row.customer_visible ? 'success' : 'info'" size="small">
                {{ row.customer_visible ? 'Visible' : 'Hidden' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="published_at" label="Published" width="180" />
          <el-table-column label="" width="220">
            <template #default="{ row }">
              <el-button
                v-if="!(row.status === 'published' && row.customer_visible)"
                size="small"
                type="primary"
                :loading="actionLoading"
                @click="onPatchOrderResource(row, { status: 'published', customer_visible: true })"
              >
                Publish
              </el-button>
              <el-button
                v-else
                size="small"
                :loading="actionLoading"
                @click="onPatchOrderResource(row, { status: 'draft', customer_visible: false })"
              >
                Unpublish
              </el-button>
              <el-button
                size="small"
                type="danger"
                plain
                :loading="actionLoading"
                @click="onPatchOrderResource(row, { status: 'archived', customer_visible: false })"
              >
                Archive
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-collapse v-if="orderResources.some(r => r.customer_visible && r.status === 'published')" class="mb">
          <el-collapse-item title="Customer visible resource preview" name="resource-preview">
            <el-table :data="orderResources.filter(r => r.customer_visible && r.status === 'published')" stripe size="small">
              <el-table-column prop="title" label="Title" />
              <el-table-column prop="category" label="Category" width="130" />
              <el-table-column prop="filename" label="File" />
              <el-table-column label="Safety" width="170">
                <template #default="{ row }">
                  <el-tag v-if="row.safety?.file_location_exposed === false" size="small" type="success">No path leak</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>
        <el-form label-width="150px" class="resource-form">
          <el-form-item label="Title">
            <el-input v-model="resourceForm.title" placeholder="Defaults to uploaded filename" />
          </el-form-item>
          <el-form-item label="Category">
            <el-select v-model="resourceForm.category" style="width: 220px">
              <el-option label="General" value="general" />
              <el-option label="Quote PDF" value="quote_pdf" />
              <el-option label="Packing List" value="packing_list" />
              <el-option label="Spec Sheet" value="spec_sheet" />
              <el-option label="Certificate" value="certificate" />
              <el-option label="Shipment" value="shipment" />
              <el-option label="Other" value="other" />
            </el-select>
          </el-form-item>
          <el-form-item label="Description">
            <el-input v-model="resourceForm.description" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item label="Publish now">
            <el-checkbox v-model="resourceForm.customer_visible" />
          </el-form-item>
          <el-form-item>
            <el-upload :show-file-list="false" :http-request="onUploadOrderResource">
              <template #trigger>
                <el-button type="primary" :loading="resourceUploading">Upload Resource</el-button>
              </template>
            </el-upload>
          </el-form-item>
        </el-form>
      </section>

      <section v-if="canCancel" class="section mb">
        <h3>Cancel Order</h3>
        <el-input v-model="cancelReason" placeholder="Reason (optional)" class="mb" style="max-width: 400px" />
        <el-button type="danger" :loading="actionLoading" @click="onCancel">Cancel Order</el-button>
      </section>

      <section class="section mb">
        <h3>Timeline</h3>
        <el-empty v-if="!timelineItems.length" description="No events" />
        <el-timeline v-else>
          <el-timeline-item v-for="(item, idx) in timelineItems" :key="idx" :timestamp="item.timestamp || ''">
            <strong>{{ item.title }}</strong>
          </el-timeline-item>
        </el-timeline>
      </section>
    </template>
    <el-empty v-else description="Order not found" />
  </div>
</template>

<style scoped>
.page { padding: 16px; }
.mb { margin-bottom: 16px; }
.section { margin-top: 24px; }
.section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.link { color: var(--el-color-primary); }
.split-detail { padding: 12px; border: 1px solid var(--el-border-color); border-radius: 4px; }
.mt { margin-top: 12px; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.summary-tile { border: 1px solid var(--el-border-color); border-radius: 4px; padding: 12px; background: #f8fafc; }
.summary-label { font-size: 12px; color: #64748b; text-transform: uppercase; }
.summary-value { margin-top: 6px; font-weight: 600; color: #0f172a; }
.customer-stage {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 12px;
  background: #f8fafc;
}
.customer-stage-title { margin-top: 4px; font-size: 18px; font-weight: 700; color: #0f172a; }
.customer-stage-copy { margin: 6px 0 0; color: #475569; }
@media (max-width: 900px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .summary-grid { grid-template-columns: 1fr; }
}
</style>
