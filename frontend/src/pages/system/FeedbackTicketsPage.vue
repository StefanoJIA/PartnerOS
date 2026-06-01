<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">Feedback Tickets</h2>
        <p class="mt-1 text-sm text-slate-600">Internal operations queue for customer portal feedback.</p>
      </div>
      <el-button type="primary" :loading="loading" @click="load">Refresh</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon :title="FEEDBACK_SAFETY_NOTE" />
    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <div class="grid gap-3 md:grid-cols-5">
      <el-select v-model="filters.status" clearable placeholder="Status">
        <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
      </el-select>
      <el-select v-model="filters.priority" clearable placeholder="Priority">
        <el-option v-for="p in priorities" :key="p" :label="p" :value="p" />
      </el-select>
      <el-input v-model="filters.feedback_type" clearable placeholder="Type" />
      <el-input v-model="filters.order_id" clearable placeholder="Order ID" @keyup.enter="load" />
      <el-input v-model="filters.search" clearable placeholder="Search" @keyup.enter="load" />
    </div>

    <el-table :data="tickets" v-loading="loading" class="w-full" @row-click="openTicket">
      <el-table-column prop="ticket_number" label="Ticket" width="150" />
      <el-table-column prop="subject" label="Subject" min-width="220" />
      <el-table-column prop="feedback_type" label="Type" width="130" />
      <el-table-column prop="status" label="Status" width="130">
        <template #default="{ row }">
          <el-tag size="small" :type="statusTag(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="Priority" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="priorityTag(row.priority)" effect="plain">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Review" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="row.operation.needs_internal_review ? 'warning' : 'success'" effect="plain">
            {{ row.operation.needs_internal_review ? 'review' : 'clear' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Age" width="90">
        <template #default="{ row }">{{ row.operation.age_days ?? '-' }}</template>
      </el-table-column>
      <el-table-column prop="internal_owner" label="Owner" width="160" />
      <el-table-column prop="created_at" label="Created" width="190" />
    </el-table>

    <div class="flex items-center justify-between text-sm text-slate-500">
      <span>Total {{ total }}</span>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="limit"
        layout="prev, pager, next"
        :total="total"
        @current-change="load"
      />
    </div>

    <el-drawer v-model="drawerOpen" size="520px" title="Feedback ticket">
      <template v-if="selected">
        <dl class="grid gap-3 text-sm">
          <div>
            <dt class="text-slate-500">Ticket</dt>
            <dd class="font-medium">{{ selected.ticket_number }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">Subject</dt>
            <dd>{{ selected.subject }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">Message</dt>
            <dd class="whitespace-pre-wrap rounded border border-slate-200 bg-slate-50 p-3">{{ selected.message }}</dd>
          </div>
          <div class="grid grid-cols-3 gap-2">
            <el-tag :type="selected.operation.activity_logging_enabled ? 'success' : 'warning'" effect="plain">
              {{ selected.operation.activity_logging_enabled ? 'activity logging' : 'not logged' }}
            </el-tag>
            <el-tag :type="selected.operation.internal_handling_only ? 'info' : 'danger'" effect="plain">
              internal handling
            </el-tag>
            <el-tag :type="selected.safety.customer_notified ? 'danger' : 'success'" effect="plain">
              {{ selected.safety.customer_notified ? 'customer notified' : 'no notification' }}
            </el-tag>
          </div>
          <div class="grid grid-cols-3 gap-2">
            <div class="rounded border border-slate-200 p-3">
              <dt class="text-slate-500">Age</dt>
              <dd class="font-medium">{{ selected.operation.age_days ?? '-' }}</dd>
            </div>
            <div class="rounded border border-slate-200 p-3">
              <dt class="text-slate-500">Review</dt>
              <dd class="font-medium">{{ selected.operation.needs_internal_review ? 'needed' : 'clear' }}</dd>
            </div>
            <div class="rounded border border-slate-200 p-3">
              <dt class="text-slate-500">Summary</dt>
              <dd class="font-medium">{{ selected.operation.response_summary_missing ? 'missing' : 'ok' }}</dd>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <dt class="text-slate-500">Customer</dt>
              <dd>{{ selected.customer_name || '-' }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Email</dt>
              <dd>{{ selected.customer_email || '-' }}</dd>
            </div>
          </div>
          <div v-if="selected.order_id">
            <dt class="text-slate-500">Related order</dt>
            <dd class="mt-1">
              <el-button size="small" @click="openRelatedOrder(selected.order_id)">Open order</el-button>
            </dd>
          </div>
        </dl>

        <el-divider />

        <el-form label-position="top">
          <el-form-item label="Status">
            <el-select v-model="form.status">
              <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
          <el-form-item label="Priority">
            <el-select v-model="form.priority">
              <el-option v-for="p in priorities" :key="p" :label="p" :value="p" />
            </el-select>
          </el-form-item>
          <el-form-item label="Internal owner">
            <el-input v-model="form.internal_owner" />
          </el-form-item>
          <el-form-item label="Response summary">
            <el-input v-model="form.response_summary" type="textarea" rows="4" />
          </el-form-item>
          <el-alert type="info" :closable="false" show-icon title="Saving this form records internal handling only. No customer notification is sent." />
          <div class="mt-4 flex flex-wrap gap-2">
            <el-button type="primary" :loading="saving" @click="save">Save</el-button>
            <el-button @click="quickStatus('resolved')">Mark resolved</el-button>
            <el-button @click="quickStatus('closed')">Close</el-button>
          </div>
        </el-form>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { formatApiError } from '@/api/errors'
import {
  FEEDBACK_SAFETY_NOTE,
  closeFeedbackTicket,
  fetchFeedbackTicket,
  fetchFeedbackTickets,
  resolveFeedbackTicket,
  updateFeedbackTicket,
  type FeedbackTicket,
  type FeedbackTicketUpdatePayload,
} from '@/api/feedbackTickets'

const statuses = ['new', 'in_review', 'responded', 'resolved', 'closed']
const priorities = ['low', 'normal', 'high', 'urgent']

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const tickets = ref<FeedbackTicket[]>([])
const selected = ref<FeedbackTicket | null>(null)
const drawerOpen = ref(false)
const total = ref(0)
const page = ref(1)
const limit = ref(50)
const filters = reactive({ status: '', priority: '', feedback_type: '', order_id: '', search: '' })
const form = reactive({ status: 'new', priority: 'normal', internal_owner: '', response_summary: '' })
const route = useRoute()
const router = useRouter()
let syncingRouteFilters = false

function statusTag(status: string): '' | 'success' | 'warning' | 'info' {
  if (status === 'resolved' || status === 'closed') return 'success'
  if (status === 'responded') return 'warning'
  if (status === 'in_review') return 'info'
  return ''
}

function priorityTag(priority: string): '' | 'danger' | 'warning' | 'info' {
  if (priority === 'urgent') return 'danger'
  if (priority === 'high') return 'warning'
  if (priority === 'low') return 'info'
  return ''
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchFeedbackTickets({
      status: filters.status || undefined,
      priority: filters.priority || undefined,
      feedback_type: filters.feedback_type || undefined,
      order_id: filters.order_id || undefined,
      search: filters.search || undefined,
      page: page.value,
      limit: limit.value,
    })
    tickets.value = data.items
    total.value = data.total
  } catch (e) {
    error.value = formatApiError(e, 'Failed to load feedback tickets.')
  } finally {
    loading.value = false
  }
}

async function openTicket(row: FeedbackTicket) {
  await openTicketById(row.id, true)
}

async function openTicketById(ticketId: string, syncRoute: boolean) {
  error.value = ''
  selected.value = await fetchFeedbackTicket(ticketId)
  syncForm()
  drawerOpen.value = true
  if (syncRoute) {
    await router.replace({ name: 'feedback-tickets', query: { ...route.query, ticket_id: ticketId } })
  }
}

function syncForm() {
  if (!selected.value) return
  form.status = selected.value.status
  form.priority = selected.value.priority
  form.internal_owner = selected.value.internal_owner || ''
  form.response_summary = selected.value.response_summary || ''
}

async function save() {
  if (!selected.value) return
  saving.value = true
  try {
    selected.value = await updateFeedbackTicket(selected.value.id, {
      status: form.status,
      priority: form.priority,
      internal_owner: form.internal_owner || null,
      response_summary: form.response_summary || null,
    })
    await load()
  } catch (e) {
    error.value = formatApiError(e, 'Failed to save feedback ticket.')
  } finally {
    saving.value = false
  }
}

function formPayload(): FeedbackTicketUpdatePayload {
  return {
    status: form.status,
    priority: form.priority,
    internal_owner: form.internal_owner || null,
    response_summary: form.response_summary || null,
  }
}

async function quickStatus(status: 'resolved' | 'closed') {
  if (!selected.value) return
  saving.value = true
  error.value = ''
  try {
    form.status = status
    selected.value =
      status === 'resolved'
        ? await resolveFeedbackTicket(selected.value.id, formPayload())
        : await closeFeedbackTicket(selected.value.id, formPayload())
    syncForm()
    await load()
  } catch (e) {
    error.value = formatApiError(e, `Failed to mark feedback ticket ${status}.`)
  } finally {
    saving.value = false
  }
}

function openRelatedOrder(orderId: string) {
  router.push({ name: 'order-detail', params: { orderId } })
}

function routeText(value: unknown): string {
  if (Array.isArray(value)) return String(value[0] || '')
  return typeof value === 'string' ? value : ''
}

function applyRouteFilters() {
  filters.status = routeText(route.query.status)
  filters.priority = routeText(route.query.priority)
  filters.feedback_type = routeText(route.query.feedback_type)
  filters.order_id = routeText(route.query.order_id)
  filters.search = routeText(route.query.search)
}

function routeFilterSnapshot() {
  return [
    routeText(route.query.status),
    routeText(route.query.priority),
    routeText(route.query.feedback_type),
    routeText(route.query.order_id),
    routeText(route.query.search),
  ].join('\u0000')
}

async function syncRouteFiltersAndLoad() {
  syncingRouteFilters = true
  applyRouteFilters()
  page.value = 1
  try {
    await load()
  } finally {
    syncingRouteFilters = false
  }
}

watch(filters, () => {
  if (syncingRouteFilters) return
  page.value = 1
  load()
})

watch(
  () => routeFilterSnapshot(),
  async () => {
    await syncRouteFiltersAndLoad()
  },
)

watch(
  () => route.query.ticket_id,
  async (ticketId) => {
    const id = routeText(ticketId)
    if (id && id !== selected.value?.id) {
      await openTicketById(id, false)
    }
  },
)

onMounted(async () => {
  await syncRouteFiltersAndLoad()
  const ticketId = routeText(route.query.ticket_id)
  if (ticketId) {
    await openTicketById(ticketId, false)
  }
})
</script>
