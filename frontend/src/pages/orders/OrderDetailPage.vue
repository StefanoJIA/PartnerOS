<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  addSupplierConfirmation,
  cancelOrder,
  confirmOrderCustomer,
  confirmationTypeWarning,
  ensurePartnerSplits,
  ensureProductionMilestones,
  fetchOrder,
  fetchOrderConfirmations,
  fetchOrderTimeline,
  fetchPartnerSplits,
  fetchPartnerSplitDetail,
  fetchProductionMilestones,
  updateProductionMilestone,
  strengthTagType,
  SUPPLIER_SAFETY_NOTE,
  PRODUCTION_SAFETY_NOTE,
  voidOrderConfirmation,
  type OrderConfirmationRecord,
  type OrderDetail,
  type OrderTimelineItem,
  type PartnerSplit,
  type ProductionMilestone,
  type SupplierConfirmationRecord,
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
const editingMilestoneId = ref<string | null>(null)
const milestoneForm = reactive({
  status: 'planned',
  planned_date: '',
  actual_date: '',
  responsible_party: '',
  notes: '',
})

const SAFETY =
  'Recording customer confirmation does not notify suppliers, start production, create shipments, confirm inventory, confirm certifications, or confirm lead time.'

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
const canCancel = computed(() => order.value && ['pending_customer_confirmation', 'confirmed'].includes(order.value.status))
const typeWarning = computed(() => confirmationTypeWarning(confirmForm.confirmation_type))
const orderWarnings = computed(() => order.value?.warnings || order.value?.confirmation_summary?.warnings || [])

async function loadPartnerSplits() {
  if (!order.value) return
  const ps = await fetchPartnerSplits(order.value.id)
  partnerSplits.value = ps.items
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
    const tl = await fetchOrderTimeline(id)
    timelineItems.value = tl.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load order'
  } finally {
    loading.value = false
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
    <el-button link type="primary" @click="router.push({ name: 'orders' })">← Orders</el-button>

    <div v-if="loading" v-loading="true" style="min-height: 160px" />
    <template v-else-if="order">
      <h1>{{ order.order_number }}</h1>
      <el-alert type="warning" :closable="false" show-icon title="Confirmation Safety" :description="SAFETY" class="mb" />
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
        <el-descriptions-item label="Status">{{ order.status }}</el-descriptions-item>
        <el-descriptions-item label="Active Confirmations">{{ order.confirmation_summary?.active_count ?? 0 }}</el-descriptions-item>
        <el-descriptions-item label="Grand Total">{{ order.currency }} {{ order.grand_total }}</el-descriptions-item>
        <el-descriptions-item label="Source Quote">
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
        <h3>Line Items</h3>
        <el-table :data="order.line_items" stripe>
          <el-table-column prop="product_name" label="Product" />
          <el-table-column prop="quantity" label="Qty" width="80" />
          <el-table-column prop="unit_price" label="Unit Price" width="120" />
          <el-table-column prop="total_price" label="Total" width="120" />
          <el-table-column prop="status" label="Status" width="120" />
        </el-table>
      </section>

      <section class="section mb">
        <div class="section-head">
          <h3>Customer Confirmations</h3>
          <el-button v-if="canAddConfirmation" type="primary" @click="showAddForm = !showAddForm">
            Add Confirmation
          </el-button>
        </div>

        <el-table :data="confirmations" stripe class="mb">
          <el-table-column prop="confirmation_type" label="Type" width="140" />
          <el-table-column label="Strength" width="100">
            <template #default="{ row }">
              <el-tag :type="strengthTagType(row.confirmation_strength)" size="small">{{ row.confirmation_strength }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="confirmed_at" label="Confirmed At" width="180" />
          <el-table-column prop="confirmed_by_name" label="By" width="120" />
          <el-table-column prop="evidence_reference" label="Evidence" />
          <el-table-column prop="status" label="Status" width="90" />
          <el-table-column label="" width="100">
            <template #default="{ row }">
              <el-button v-if="row.status === 'active'" size="small" @click="onVoid(row)">Void</el-button>
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
</style>
