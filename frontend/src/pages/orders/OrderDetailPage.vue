<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  cancelOrder,
  confirmOrderCustomer,
  confirmationTypeWarning,
  fetchOrder,
  fetchOrderConfirmations,
  fetchOrderTimeline,
  strengthTagType,
  voidOrderConfirmation,
  type OrderConfirmationRecord,
  type OrderDetail,
  type OrderTimelineItem,
} from '@/api/orders'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const order = ref<OrderDetail | null>(null)
const confirmations = ref<OrderConfirmationRecord[]>([])
const timelineItems = ref<OrderTimelineItem[]>([])
const actionLoading = ref(false)
const successMsg = ref('')
const showAddForm = ref(false)

const SAFETY =
  'Recording customer confirmation does not notify suppliers, start production, create shipments, confirm inventory, confirm certifications, or confirm lead time.'

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
const canCancel = computed(() => order.value && ['pending_customer_confirmation', 'confirmed'].includes(order.value.status))
const typeWarning = computed(() => confirmationTypeWarning(confirmForm.confirmation_type))
const orderWarnings = computed(() => order.value?.warnings || order.value?.confirmation_summary?.warnings || [])

async function load() {
  loading.value = true
  error.value = ''
  try {
    const id = route.params.orderId as string
    order.value = await fetchOrder(id)
    const conf = await fetchOrderConfirmations(id)
    confirmations.value = conf.items
    const tl = await fetchOrderTimeline(id)
    timelineItems.value = tl.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load order'
  } finally {
    loading.value = false
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
</style>
