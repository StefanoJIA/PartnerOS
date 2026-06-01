<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">Portal Customer Bridge UAT</h2>
        <p class="mt-1 text-sm text-slate-600">Internal staging checks for the service portal consumer contract.</p>
      </div>
      <el-button type="primary" :loading="readinessLoading" @click="loadReadiness">Refresh readiness</el-button>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="Token entry is masked and kept only in this page state. TEST feedback must stay clearly marked as TEST."
    />
    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <section class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Portal API</p>
        <el-tag class="mt-2" :type="readiness?.enabled ? 'success' : 'danger'">
          {{ readiness?.enabled ? 'enabled' : 'disabled' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Token</p>
        <el-tag class="mt-2" :type="readiness?.token_configured ? 'success' : 'warning'">
          {{ readiness?.token_configured ? 'configured' : 'not configured' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">CORS origins</p>
        <el-tag class="mt-2" :type="readiness?.allowed_origins_configured ? 'success' : 'warning'">
          {{ readiness?.allowed_origins_configured ? 'configured' : 'not configured' }}
        </el-tag>
      </div>
      <div class="rounded border border-slate-200 bg-white p-4">
        <p class="text-sm text-slate-500">Forbidden checks</p>
        <el-tag class="mt-2" :type="forbiddenSummary.length ? 'danger' : 'success'">
          {{ forbiddenSummary.length ? `${forbiddenSummary.length} hit(s)` : 'clear' }}
        </el-tag>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
        <el-input v-model="portalToken" type="password" show-password placeholder="Portal staging token" autocomplete="off" />
        <el-input v-model="orderId" placeholder="Order ID for detail checks" />
        <el-button :loading="running" type="primary" @click="runCoreChecks">Run checks</el-button>
      </div>
      <div class="mt-3 flex flex-wrap gap-2">
        <el-button size="small" @click="runCheck('products')">Products</el-button>
        <el-button size="small" @click="runCheck('orders')">Orders</el-button>
        <el-button size="small" :disabled="!orderId" @click="runOrderChecks">Order views</el-button>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">TEST feedback</h3>
        <el-button :loading="feedbackLoading" type="primary" @click="submitFeedback">Create TEST ticket</el-button>
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <el-input v-model="feedback.order_id" placeholder="Order ID optional" />
        <el-input v-model="feedback.customer_email" placeholder="Customer email optional" />
        <el-select v-model="feedback.feedback_type">
          <el-option label="tracking" value="tracking" />
          <el-option label="resource" value="resource" />
          <el-option label="general" value="general" />
        </el-select>
        <el-select v-model="feedback.priority">
          <el-option label="normal" value="normal" />
          <el-option label="high" value="high" />
          <el-option label="urgent" value="urgent" />
        </el-select>
      </div>
      <el-input v-model="feedback.subject" class="mt-3" />
      <el-input v-model="feedback.message" class="mt-3" type="textarea" rows="3" />
    </section>

    <el-table :data="results" class="w-full">
      <el-table-column prop="name" label="Check" width="180" />
      <el-table-column prop="status" label="HTTP" width="100" />
      <el-table-column label="Result" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="row.ok ? 'success' : 'danger'">{{ row.ok ? 'PASS' : 'FAIL' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Forbidden fields">
        <template #default="{ row }">
          <span v-if="!row.forbiddenHits.length" class="text-slate-500">none</span>
          <el-tag v-for="hit in row.forbiddenHits" v-else :key="hit" class="mr-1" type="danger" size="small">
            {{ hit }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <el-collapse v-if="results.length">
      <el-collapse-item v-for="row in results" :key="row.name" :title="row.name">
        <pre class="overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">{{ pretty(row.data) }}</pre>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { formatApiError } from '@/api/errors'
import {
  fetchPortalCustomerReadiness,
  portalCustomerContract,
  type PortalReadiness,
  type PortalResult,
} from '@/api/portalCustomer'

const readiness = ref<PortalReadiness | null>(null)
const readinessLoading = ref(false)
const running = ref(false)
const feedbackLoading = ref(false)
const error = ref('')
const portalToken = ref('')
const orderId = ref('')
const results = ref<(PortalResult & { name: string })[]>([])
const feedback = reactive({
  order_id: '',
  feedback_type: 'tracking',
  subject: 'TEST D7.8 portal UAT feedback',
  message: 'TEST: service portal staging integration feedback. No customer notification expected.',
  priority: 'normal',
  customer_name: 'TEST Portal User',
  customer_email: '',
})

const forbiddenSummary = computed(() => Array.from(new Set(results.value.flatMap((r) => r.forbiddenHits))))

function pretty(value: unknown) {
  return JSON.stringify(value, null, 2)
}

async function loadReadiness() {
  readinessLoading.value = true
  error.value = ''
  try {
    readiness.value = await fetchPortalCustomerReadiness()
  } catch (e) {
    error.value = formatApiError(e, 'Failed to load portal readiness.')
  } finally {
    readinessLoading.value = false
  }
}

async function pushResult(name: string, promise: Promise<PortalResult>) {
  const result = await promise
  results.value = [...results.value.filter((r) => r.name !== name), { name, ...result }]
}

async function runCheck(name: 'products' | 'orders') {
  running.value = true
  try {
    await pushResult(name, portalCustomerContract[name](portalToken.value))
  } finally {
    running.value = false
  }
}

async function runOrderChecks() {
  if (!orderId.value) return
  running.value = true
  try {
    await Promise.all([
      pushResult('order detail', portalCustomerContract.orderDetail(portalToken.value, orderId.value)),
      pushResult('snapshot', portalCustomerContract.orderSnapshot(portalToken.value, orderId.value)),
      pushResult('production', portalCustomerContract.production(portalToken.value, orderId.value)),
      pushResult('shipment', portalCustomerContract.shipment(portalToken.value, orderId.value)),
      pushResult('resources', portalCustomerContract.resources(portalToken.value, orderId.value)),
    ])
  } finally {
    running.value = false
  }
}

async function runCoreChecks() {
  results.value = []
  await Promise.all([runCheck('products'), runCheck('orders')])
  if (orderId.value) await runOrderChecks()
}

async function submitFeedback() {
  feedbackLoading.value = true
  try {
    await pushResult(
      'feedback',
      portalCustomerContract.feedback(portalToken.value, {
        order_id: feedback.order_id || undefined,
        feedback_type: feedback.feedback_type,
        subject: feedback.subject.startsWith('TEST') ? feedback.subject : `TEST ${feedback.subject}`,
        message: feedback.message.includes('TEST') ? feedback.message : `TEST: ${feedback.message}`,
        priority: feedback.priority,
        customer_name: feedback.customer_name,
        customer_email: feedback.customer_email || undefined,
      }),
    )
  } finally {
    feedbackLoading.value = false
  }
}

onMounted(loadReadiness)
</script>
