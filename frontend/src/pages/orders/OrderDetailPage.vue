<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  cancelOrder,
  confirmOrderCustomer,
  fetchOrder,
  fetchOrderTimeline,
  type OrderDetail,
  type OrderTimelineItem,
} from '@/api/orders'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const order = ref<OrderDetail | null>(null)
const timelineItems = ref<OrderTimelineItem[]>([])
const actionLoading = ref(false)
const successMsg = ref('')

const SAFETY =
  'This order does not start production, notify suppliers, create shipments, or confirm inventory, certifications, or lead times. Supplier confirmation is not started in D7.2.'

const confirmForm = reactive({
  confirmation_type: 'email',
  note: '',
})

const cancelReason = ref('')

const canConfirm = computed(() => order.value?.status === 'pending_customer_confirmation')
const canCancel = computed(() => order.value && ['pending_customer_confirmation', 'confirmed'].includes(order.value.status))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const id = route.params.orderId as string
    order.value = await fetchOrder(id)
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
  try {
    order.value = await confirmOrderCustomer(order.value.id, {
      confirmation_type: confirmForm.confirmation_type,
      note: confirmForm.note || undefined,
    })
    successMsg.value = 'Customer confirmation recorded.'
    const tl = await fetchOrderTimeline(order.value.id)
    timelineItems.value = tl.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Confirm failed'
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
      <el-alert type="warning" :closable="false" show-icon title="Order Safety" :description="SAFETY" class="mb" />
      <el-alert v-if="error" type="error" :title="error" show-icon class="mb" @close="error = ''" />
      <el-alert v-if="successMsg" type="success" :title="successMsg" show-icon class="mb" @close="successMsg = ''" />

      <el-descriptions :column="2" border class="mb">
        <el-descriptions-item label="Status">{{ order.status }}</el-descriptions-item>
        <el-descriptions-item label="Order Date">{{ order.order_date }}</el-descriptions-item>
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
        <el-descriptions-item label="Bill To">{{ order.bill_to_company || order.bill_to_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="Ship To">{{ order.ship_to_company || order.ship_to_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="Payment Terms">{{ order.payment_terms || '—' }}</el-descriptions-item>
        <el-descriptions-item label="Shipping Terms">{{ order.shipping_terms || '—' }}</el-descriptions-item>
      </el-descriptions>

      <section class="section mb">
        <h3>Line Items</h3>
        <el-table :data="order.line_items" stripe>
          <el-table-column prop="product_name" label="Product" />
          <el-table-column prop="quantity" label="Qty" width="80" />
          <el-table-column prop="unit_price" label="Unit Price" width="120" />
          <el-table-column prop="total_price" label="Total" width="120" />
          <el-table-column prop="incoterm" label="Incoterm" width="100" />
          <el-table-column prop="status" label="Status" width="120" />
        </el-table>
      </section>

      <section v-if="canConfirm" class="section mb">
        <h3>Confirm Customer</h3>
        <el-form inline @submit.prevent="onConfirm">
          <el-form-item label="Type">
            <el-select v-model="confirmForm.confirmation_type" style="width: 180px">
              <el-option label="Email" value="email" />
              <el-option label="Purchase Order" value="purchase_order" />
              <el-option label="Signed Quote" value="signed_quote" />
              <el-option label="Verbal" value="verbal" />
              <el-option label="Internal Note" value="internal_note" />
            </el-select>
          </el-form-item>
          <el-form-item label="Note">
            <el-input v-model="confirmForm.note" placeholder="Confirmation note" style="width: 280px" />
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
.link { color: var(--el-color-primary); }
</style>
