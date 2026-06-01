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
        <el-button size="small" type="primary" plain @click="runReadPathChecks">Read path</el-button>
        <el-button size="small" @click="runCheck('manifest')">Manifest</el-button>
        <el-button size="small" @click="runCheck('products')">Products</el-button>
        <el-button size="small" @click="runCheck('orders')">Orders</el-button>
        <el-button size="small" :disabled="!orderId" @click="runOrderChecks">Order views</el-button>
      </div>
      <p class="mt-2 text-xs text-slate-500">
        Read path is read-only: it checks manifest, products, orders, then uses the first returned order for detail, snapshot, production, shipment, and resources.
      </p>
    </section>

    <section v-if="portalDisplayPreview" class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 class="font-semibold text-slate-800">Service Portal preview</h3>
          <p class="mt-1 text-sm text-slate-500">{{ portalDisplayPreview.headline }}</p>
        </div>
        <el-tag :type="portalDisplayPreview.planned_dates_are_guarantees ? 'danger' : 'success'" effect="plain">
          {{ portalDisplayPreview.planned_dates_are_guarantees ? 'date guarantee risk' : 'planned dates only' }}
        </el-tag>
      </div>
      <div class="grid gap-3 md:grid-cols-[1fr_220px]">
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Current stage</p>
          <p class="mt-1 font-medium text-slate-800">{{ portalDisplayPreview.current_step_label || portalDisplayPreview.stage_label }}</p>
          <el-progress class="mt-3" :percentage="portalDisplayPreview.progress_percent" />
          <p class="mt-3 text-sm font-medium text-slate-700">{{ portalDisplayPreview.next_action_label }}</p>
          <p class="mt-1 text-sm text-slate-500">{{ portalDisplayPreview.next_action_detail }}</p>
        </div>
        <div class="rounded border border-slate-200 p-3">
          <p class="text-sm text-slate-500">Feedback CTA</p>
          <p class="mt-1 font-medium text-slate-800">{{ portalDisplayPreview.feedback_cta.label }}</p>
          <p class="mt-1 break-all text-xs text-slate-500">{{ portalDisplayPreview.feedback_cta.path }}</p>
          <div class="mt-2 flex flex-wrap gap-1">
            <el-tag size="small" :type="portalDisplayPreview.feedback_cta.automatic_reply_sent ? 'danger' : 'success'" effect="plain">
              {{ portalDisplayPreview.feedback_cta.automatic_reply_sent ? 'auto reply risk' : 'no auto reply' }}
            </el-tag>
            <el-tag size="small" :type="portalDisplayPreview.feedback_cta.customer_notified ? 'danger' : 'success'" effect="plain">
              {{ portalDisplayPreview.feedback_cta.customer_notified ? 'notified' : 'not notified' }}
            </el-tag>
          </div>
        </div>
      </div>
      <div class="mt-3 flex flex-wrap gap-2">
        <el-tag
          v-for="card in portalDisplayPreview.signal_cards"
          :key="card.key"
          :type="card.active ? (card.key === 'feedback' ? 'warning' : 'success') : 'info'"
          effect="plain"
        >
          {{ card.label }} {{ card.count }}
        </el-tag>
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
      <div v-if="feedbackNextLinks.length" class="mt-4 rounded border border-slate-200 p-3">
        <p class="text-sm font-medium text-slate-700">Returned next links</p>
        <div class="mt-2 flex flex-wrap gap-2">
          <el-button
            v-for="link in feedbackNextLinks"
            :key="link.key"
            size="small"
            :disabled="!link.path"
            @click="runFeedbackNextLink(link.key)"
          >
            {{ link.label }}
          </el-button>
        </div>
        <p class="mt-2 text-xs text-slate-500">These are customer Portal API paths returned by PartnerOS; no internal ticket ID or token value is exposed.</p>
      </div>
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
type NamedPortalResult = PortalResult & { name: string }
type PortalDisplayPreview = {
  headline: string
  stage: string
  stage_label: string
  current_step_label: string | null
  next_action_label: string
  next_action_detail: string
  progress_percent: number
  signal_cards: Array<{ key: string; label: string; active: boolean; count: number }>
  feedback_cta: {
    label: string
    path: string
    customer_notified: boolean
    automatic_reply_sent: boolean
    resolution_time_promised: boolean
  }
  planned_dates_are_guarantees: boolean
}

const results = ref<NamedPortalResult[]>([])
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
const portalDisplayPreview = computed<PortalDisplayPreview | null>(() => {
  const snapshotResult = [...results.value].reverse().find((r) => r.name.includes('snapshot'))
  const envelope = snapshotResult?.data as { data?: { portal_display?: PortalDisplayPreview } } | undefined
  return envelope?.data?.portal_display || null
})
const feedbackNextLinks = computed(() => {
  const feedbackResult = results.value.find((r) => r.name === 'feedback')
  const envelope = feedbackResult?.data as { data?: { next_links?: Record<string, string | null> } } | undefined
  const links = envelope?.data?.next_links || {}
  return [
    { key: 'orders', label: 'Orders', path: links.orders },
    { key: 'order_snapshot', label: 'Snapshot', path: links.order_snapshot },
    { key: 'production', label: 'Production', path: links.production },
    { key: 'shipment', label: 'Shipment', path: links.shipment },
    { key: 'resources', label: 'Resources', path: links.resources },
  ].filter((item) => item.path !== undefined)
})

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
  return result
}

async function runCheck(name: 'manifest' | 'products' | 'orders') {
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

function firstOrderIdFrom(result: PortalResult) {
  if (!result.ok || !result.data || typeof result.data !== 'object') return ''
  const envelope = result.data as { data?: { items?: Array<{ id?: string }> } }
  return envelope.data?.items?.find((item) => typeof item.id === 'string')?.id || ''
}

async function runReadPathChecks() {
  results.value = []
  running.value = true
  try {
    await pushResult('manifest', portalCustomerContract.manifest(portalToken.value))
    await pushResult('products', portalCustomerContract.products(portalToken.value))
    const orders = await pushResult('orders', portalCustomerContract.orders(portalToken.value))
    const firstOrderId = firstOrderIdFrom(orders)
    if (firstOrderId) {
      orderId.value = firstOrderId
      if (!feedback.order_id) feedback.order_id = firstOrderId
      await runOrderChecks()
    }
  } finally {
    running.value = false
  }
}

async function runCoreChecks() {
  results.value = []
  await Promise.all([runCheck('manifest'), runCheck('products'), runCheck('orders')])
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

function orderIdFromPortalPath(path: string | null | undefined) {
  if (!path) return ''
  return path.match(/\/orders\/([^/]+)/)?.[1] || ''
}

async function runFeedbackNextLink(key: string) {
  const link = feedbackNextLinks.value.find((item) => item.key === key)
  if (!link?.path) return
  if (key === 'orders') {
    await pushResult('orders after feedback', portalCustomerContract.orders(portalToken.value))
    return
  }
  const linkedOrderId = orderIdFromPortalPath(link.path)
  if (!linkedOrderId) return
  orderId.value = linkedOrderId
  if (key === 'order_snapshot') {
    await pushResult('snapshot after feedback', portalCustomerContract.orderSnapshot(portalToken.value, linkedOrderId))
  } else if (key === 'production') {
    await pushResult('production after feedback', portalCustomerContract.production(portalToken.value, linkedOrderId))
  } else if (key === 'shipment') {
    await pushResult('shipment after feedback', portalCustomerContract.shipment(portalToken.value, linkedOrderId))
  } else if (key === 'resources') {
    await pushResult('resources after feedback', portalCustomerContract.resources(portalToken.value, linkedOrderId))
  }
}

onMounted(loadReadiness)
</script>
