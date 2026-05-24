<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchOrders, type OrderSummary } from '@/api/orders'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const items = ref<OrderSummary[]>([])
const statusFilter = ref('')

const SAFETY =
  'Customer orders are created manually from sent quotes. Order creation does not start production, notify suppliers, create shipments, or confirm inventory, certifications, or lead times.'

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchOrders({ status: statusFilter.value || undefined })
    items.value = data.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load orders'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <h1>Customer Orders</h1>
    <el-alert type="warning" :closable="false" show-icon title="Safety" :description="SAFETY" class="mb" />

    <div class="toolbar">
      <el-select v-model="statusFilter" placeholder="Status" clearable style="width: 240px" @change="load">
        <el-option label="Pending Customer Confirmation" value="pending_customer_confirmation" />
        <el-option label="Confirmed" value="confirmed" />
        <el-option label="Cancelled" value="cancelled" />
      </el-select>
    </div>

    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />
    <div v-if="loading" v-loading="true" style="min-height: 120px" />
    <el-table
      v-else
      :data="items"
      stripe
      @row-click="(row: OrderSummary) => router.push({ name: 'order-detail', params: { orderId: row.id } })"
    >
      <el-table-column prop="order_number" label="Order #" width="140" />
      <el-table-column prop="bill_to_company" label="Company" />
      <el-table-column prop="status" label="Status" width="220" />
      <el-table-column prop="grand_total" label="Total" width="140">
        <template #default="{ row }">{{ row.currency }} {{ row.grand_total }}</template>
      </el-table-column>
      <el-table-column prop="order_date" label="Order Date" width="120" />
      <el-table-column label="Source Quote" width="140">
        <template #default="{ row }">
          <router-link
            class="link"
            :to="{ name: 'quote-detail', params: { id: row.source_quote_id } }"
            @click.stop
          >
            View Quote
          </router-link>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.page { padding: 16px; }
.mb { margin-bottom: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.link { color: var(--el-color-primary); }
</style>
