<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">Portal Operations</h2>
        <p class="mt-1 text-sm text-slate-600">Internal launch console for customer-visible Portal data.</p>
      </div>
      <el-button type="primary" :loading="loading" @click="load">Refresh</el-button>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="Read-only operations view. No customer notification, supplier notification, carrier API call, or order status mutation is performed."
    />
    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <section class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Portal API</p>
        <el-tag class="mt-2" :type="data?.status.enabled ? 'success' : 'danger'">
          {{ data?.status.enabled ? 'enabled' : 'disabled' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Token</p>
        <el-tag class="mt-2" :type="data?.status.token_configured ? 'success' : 'warning'">
          {{ data?.status.token_configured ? 'configured' : 'missing' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Public base URL</p>
        <el-tag class="mt-2" :type="data?.status.public_base_url_configured ? 'success' : 'warning'">
          {{ data?.status.public_base_url_configured ? 'configured' : 'missing' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Forbidden field audit</p>
        <el-tag class="mt-2" :type="data?.forbidden_field_audit.hits.length ? 'danger' : 'success'">
          {{ data?.forbidden_field_audit.hits.length ? `${data.forbidden_field_audit.hits.length} hit(s)` : 'clear' }}
        </el-tag>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">Endpoint readiness</h3>
        <el-tag :type="data?.status.ready ? 'success' : 'warning'">{{ data?.status.ready ? 'ready' : 'needs config' }}</el-tag>
      </div>
      <div class="grid gap-2 md:grid-cols-3 xl:grid-cols-6">
        <div v-for="(ready, name) in data?.endpoint_readiness || {}" :key="name" class="rounded border border-slate-200 p-3">
          <p class="text-sm capitalize text-slate-600">{{ name }}</p>
          <el-tag class="mt-2" size="small" :type="ready ? 'success' : 'danger'">{{ ready ? 'ready' : 'not ready' }}</el-tag>
        </div>
      </div>
      <div v-if="data?.status.missing_config.length" class="mt-3 flex flex-wrap gap-2">
        <el-tag v-for="item in data.status.missing_config" :key="item" type="warning" effect="plain">{{ item }}</el-tag>
      </div>
    </section>

    <section class="grid gap-4 xl:grid-cols-[1.3fr_1fr]">
      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">Recent customer-visible orders</h3>
        <el-table :data="data?.recent_customer_visible_orders.items || []" v-loading="loading" class="w-full">
          <el-table-column prop="order_number" label="Order" width="160" />
          <el-table-column prop="company_name" label="Company" min-width="180" />
          <el-table-column prop="status" label="Status" width="170" />
          <el-table-column label="Total" width="150">
            <template #default="{ row }">{{ row.grand_total || '-' }} {{ row.currency }}</template>
          </el-table-column>
        </el-table>
      </div>

      <div class="rounded border border-slate-200 bg-white p-4">
        <h3 class="mb-3 font-semibold text-slate-800">Shipment status</h3>
        <div class="flex flex-wrap gap-2">
          <el-tag v-for="(count, status) in data?.shipment_status_counts || {}" :key="status" effect="plain">
            {{ status }} {{ count }}
          </el-tag>
          <span v-if="!Object.keys(data?.shipment_status_counts || {}).length" class="text-sm text-slate-500">No shipment plans</span>
        </div>
        <h3 class="mb-3 mt-5 font-semibold text-slate-800">Feedback status</h3>
        <div class="flex flex-wrap gap-2">
          <el-tag v-for="(count, status) in data?.feedback_status_counts || {}" :key="status" effect="plain">
            {{ status }} {{ count }}
          </el-tag>
          <span v-if="!Object.keys(data?.feedback_status_counts || {}).length" class="text-sm text-slate-500">No tickets</span>
        </div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <h3 class="mb-3 font-semibold text-slate-800">Customer snapshots</h3>
      <el-table :data="data?.customer_snapshots || []" class="w-full">
        <el-table-column label="Order" width="170">
          <template #default="{ row }">{{ row.order.order_number }}</template>
        </el-table-column>
        <el-table-column label="Customer stage" min-width="220">
          <template #default="{ row }">
            <div class="font-medium text-slate-800">{{ row.customer_status.label }}</div>
            <div class="text-xs text-slate-500">{{ row.customer_status.stage }}</div>
          </template>
        </el-table-column>
        <el-table-column label="Shipment" width="160">
          <template #default="{ row }">active {{ row.shipment.active_count }}</template>
        </el-table-column>
        <el-table-column label="Open feedback" width="150">
          <template #default="{ row }">{{ row.feedback.open_count }}</template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <h3 class="mb-3 font-semibold text-slate-800">Recent feedback tickets</h3>
      <el-table :data="data?.recent_feedback_tickets || []" class="w-full">
        <el-table-column prop="ticket_number" label="Ticket" width="150" />
        <el-table-column prop="subject" label="Subject" min-width="220" />
        <el-table-column prop="feedback_type" label="Type" width="130" />
        <el-table-column prop="status" label="Status" width="130" />
        <el-table-column prop="priority" label="Priority" width="120" />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { formatApiError } from '@/api/errors'
import { fetchPortalOperationsConsole, type PortalOperationsConsole } from '@/api/portalOperations'

const data = ref<PortalOperationsConsole | null>(null)
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchPortalOperationsConsole()
  } catch (e) {
    error.value = formatApiError(e, 'Failed to load Portal operations console.')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
