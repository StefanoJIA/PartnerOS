<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-semibold text-slate-900">Partner operations</h1>
        <p class="mt-1 text-sm text-slate-600">Read-only execution view across partner splits, production, and shipment readiness.</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="load">Refresh</el-button>
    </div>

    <el-alert
      v-if="dashboard && dashboard.safety.read_only"
      type="info"
      :closable="false"
      show-icon
      title="Read-only dashboard: no supplier notification, customer notification, shipment creation, or order status change is performed."
    />

    <el-skeleton v-if="loading && !dashboard" animated :rows="6" />
    <el-alert v-else-if="error" type="error" :closable="false" show-icon :title="error" />

    <template v-else-if="dashboard">
      <section class="grid gap-3 md:grid-cols-4">
        <div v-for="metric in metrics" :key="metric.label" class="rounded border border-slate-200 bg-white p-3">
          <div class="text-xs uppercase text-slate-500">{{ metric.label }}</div>
          <div class="mt-1 text-2xl font-semibold text-slate-900">{{ metric.value }}</div>
        </div>
      </section>

      <el-table :data="dashboard.items" border class="w-full" empty-text="No partner splits yet">
        <el-table-column label="Partner" min-width="220">
          <template #default="{ row }">
            <div class="font-medium text-slate-900">{{ row.partner_name }}</div>
            <div class="text-xs text-slate-500">{{ row.partner_type || 'Unclassified' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="Workload" min-width="150">
          <template #default="{ row }">
            <div>{{ row.split_count }} split(s) / {{ row.order_count }} order(s)</div>
            <div class="text-xs text-slate-500">{{ row.line_item_count }} line item(s)</div>
          </template>
        </el-table-column>
        <el-table-column label="Supplier" min-width="170">
          <template #default="{ row }">
            <StatusChips :counts="row.supplier_confirmation_status_counts" />
          </template>
        </el-table-column>
        <el-table-column label="Production" min-width="190">
          <template #default="{ row }">
            <StatusChips :counts="row.milestone_status_counts" />
            <div class="mt-1 text-xs text-slate-500">
              delayed {{ row.delayed_milestone_count }} / blocked {{ row.blocked_milestone_count }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="Shipment" min-width="170">
          <template #default="{ row }">
            <StatusChips :counts="row.shipment_status_counts" />
            <div class="mt-1 text-xs text-slate-500">active {{ row.active_shipment_count }}</div>
          </template>
        </el-table-column>
        <el-table-column label="Next ready" width="130" prop="next_expected_ready_date" />
        <el-table-column label="Risk" min-width="220">
          <template #default="{ row }">
            <div v-if="row.risk_flags.length" class="flex flex-wrap gap-1">
              <el-tag v-for="flag in row.risk_flags" :key="flag" type="warning" size="small">
                {{ flagLabel(flag) }}
              </el-tag>
            </div>
            <span v-else class="text-sm text-slate-500">No open risk</span>
          </template>
        </el-table-column>
      </el-table>
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

const StatusChips = defineComponent({
  props: {
    counts: { type: Object, required: true },
  },
  setup(props) {
    return () => {
      const entries = Object.entries(props.counts as Record<string, number>)
      if (!entries.length) return h('span', { class: 'text-sm text-slate-500' }, 'None')
      return h(
        'div',
        { class: 'flex flex-wrap gap-1' },
        entries.map(([key, value]) =>
          h(ElTag, { key, size: 'small', type: key.includes('delayed') || key.includes('blocked') ? 'warning' : 'info' }, () => `${key}: ${value}`),
        ),
      )
    }
  },
})

const metrics = computed(() => {
  const summary = dashboard.value?.summary
  if (!summary) return []
  return [
    { label: 'Partners', value: summary.partner_count },
    { label: 'Splits', value: summary.split_count },
    { label: 'Open supplier confirmations', value: summary.supplier_open_split_count },
    { label: 'Delayed / blocked milestones', value: `${summary.delayed_milestone_count} / ${summary.blocked_milestone_count}` },
    { label: 'Active shipments', value: summary.active_shipment_count },
    { label: 'Shipped or delivered', value: summary.shipped_or_delivered_count },
    { label: 'Orders covered', value: summary.order_count },
    { label: 'Confirmed splits', value: summary.supplier_confirmed_split_count },
  ]
})

function flagLabel(flag: string) {
  return flag.replaceAll('_', ' ')
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    dashboard.value = await fetchPartnerOperationsDashboard()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Partner operations dashboard unavailable'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
