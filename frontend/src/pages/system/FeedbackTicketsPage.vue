<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">客户反馈工单</h2>
        <p class="mt-1 text-sm text-slate-600">客户 Portal 反馈的内部运营队列。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon :title="FEEDBACK_SAFETY_NOTE" />
    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="font-semibold text-slate-800">反馈运营闭环</h3>
          <p class="mt-1 text-sm text-slate-600">
            用此队列把客户 Portal 反馈连接回订单详情、物流跟进和市场响应复核。除非人工在 PartnerOS 外沟通，否则更新只保留在内部。
          </p>
        </div>
        <el-tag type="info" effect="plain">仅内部处理</el-tag>
      </div>
      <div class="grid gap-3 md:grid-cols-3">
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">订单上下文</p>
          <p class="mt-1 text-sm text-slate-700">打开关联订单，检查生产、物流和客户可见状态。</p>
        </div>
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">物流跟进</p>
          <p class="mt-1 text-sm text-slate-700">物流问题转为内部行动项，不触发承运商自动化。</p>
        </div>
        <div class="rounded border border-slate-100 bg-slate-50 p-3">
          <p class="text-xs uppercase text-slate-500">市场响应</p>
          <p class="mt-1 text-sm text-slate-700">重复反馈会成为人工审查的产品或 partner 信号。</p>
        </div>
      </div>
    </section>

    <div class="grid gap-3 md:grid-cols-6">
      <el-select v-model="filters.status" clearable placeholder="状态">
        <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
      </el-select>
      <el-select v-model="filters.priority" clearable placeholder="优先级">
        <el-option v-for="p in priorities" :key="p" :label="p" :value="p" />
      </el-select>
      <el-select v-model="filters.operation_filter" clearable placeholder="运营队列">
        <el-option v-for="item in operationFilters" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-input v-model="filters.feedback_type" clearable placeholder="类型" />
      <el-input v-model="filters.order_id" clearable placeholder="Order ID" @keyup.enter="load" />
      <el-input v-model="filters.search" clearable placeholder="搜索" @keyup.enter="load" />
    </div>

    <el-table :data="tickets" v-loading="loading" class="w-full" @row-click="openTicket">
      <el-table-column prop="ticket_number" label="工单" width="150" />
      <el-table-column prop="subject" label="主题" min-width="220" />
      <el-table-column prop="feedback_type" label="类型" width="130" />
      <el-table-column prop="status" label="状态" width="130">
        <template #default="{ row }">
          <el-tag size="small" :type="statusTag(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="priorityTag(row.priority)" effect="plain">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="复核" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="row.operation.needs_internal_review ? 'warning' : 'success'" effect="plain">
            {{ row.operation.needs_internal_review ? '需复核' : '通过' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="天数" width="90">
        <template #default="{ row }">{{ row.operation.age_days ?? '-' }}</template>
      </el-table-column>
      <el-table-column prop="internal_owner" label="负责人" width="160" />
      <el-table-column prop="created_at" label="创建时间" width="190" />
    </el-table>

    <div class="flex items-center justify-between text-sm text-slate-500">
      <span>共 {{ total }} 条</span>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="limit"
        layout="prev, pager, next"
        :total="total"
        @current-change="load"
      />
    </div>

    <el-drawer v-model="drawerOpen" size="520px" title="反馈工单">
      <template v-if="selected">
        <dl class="grid gap-3 text-sm">
          <div>
            <dt class="text-slate-500">工单</dt>
            <dd class="font-medium">{{ selected.ticket_number }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">主题</dt>
            <dd>{{ selected.subject }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">消息</dt>
            <dd class="whitespace-pre-wrap rounded border border-slate-200 bg-slate-50 p-3">{{ selected.message }}</dd>
          </div>
          <div class="grid grid-cols-3 gap-2">
            <el-tag :type="selected.operation.activity_logging_enabled ? 'success' : 'warning'" effect="plain">
              {{ selected.operation.activity_logging_enabled ? '已记录活动' : '未记录' }}
            </el-tag>
            <el-tag :type="selected.operation.internal_handling_only ? 'info' : 'danger'" effect="plain">
              内部处理
            </el-tag>
            <el-tag :type="selected.safety.customer_notified ? 'danger' : 'success'" effect="plain">
              {{ selected.safety.customer_notified ? '已通知客户' : '未通知客户' }}
            </el-tag>
          </div>
          <div class="grid grid-cols-3 gap-2">
            <div class="rounded border border-slate-200 p-3">
              <dt class="text-slate-500">天数</dt>
              <dd class="font-medium">{{ selected.operation.age_days ?? '-' }}</dd>
            </div>
            <div class="rounded border border-slate-200 p-3">
              <dt class="text-slate-500">复核</dt>
              <dd class="font-medium">{{ selected.operation.needs_internal_review ? '需要' : '通过' }}</dd>
            </div>
            <div class="rounded border border-slate-200 p-3">
              <dt class="text-slate-500">摘要</dt>
              <dd class="font-medium">{{ selected.operation.response_summary_missing ? '缺失' : '已填' }}</dd>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <dt class="text-slate-500">客户</dt>
              <dd>{{ selected.customer_name || '-' }}</dd>
            </div>
            <div>
              <dt class="text-slate-500">Email</dt>
              <dd>{{ selected.customer_email || '-' }}</dd>
            </div>
          </div>
          <div v-if="selected.order_id">
            <dt class="text-slate-500">关联订单</dt>
            <dd class="mt-1">
              <el-button size="small" @click="openRelatedOrder(selected.order_id)">打开订单</el-button>
            </dd>
          </div>
        </dl>

        <el-divider />

        <el-form label-position="top">
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="form.priority">
              <el-option v-for="p in priorities" :key="p" :label="p" :value="p" />
            </el-select>
          </el-form-item>
          <el-form-item label="内部负责人">
            <el-input v-model="form.internal_owner" />
          </el-form-item>
          <el-form-item label="处理摘要">
            <el-input v-model="form.response_summary" type="textarea" rows="4" />
          </el-form-item>
          <el-alert type="info" :closable="false" show-icon title="保存只记录内部处理，不会通知客户。" />
          <div class="mt-4 flex flex-wrap gap-2">
            <el-button type="primary" :loading="saving" @click="save">保存</el-button>
            <el-button @click="quickStatus('resolved')">标记已解决</el-button>
            <el-button @click="quickStatus('closed')">关闭</el-button>
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
const operationFilters = [
  { value: 'needs_internal_review', label: '需要复核' },
  { value: 'response_summary_missing', label: '缺少摘要' },
  { value: 'ready_to_close', label: '可关闭' },
  { value: 'open', label: '未结工单' },
]

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const tickets = ref<FeedbackTicket[]>([])
const selected = ref<FeedbackTicket | null>(null)
const drawerOpen = ref(false)
const total = ref(0)
const page = ref(1)
const limit = ref(50)
const filters = reactive({ status: '', priority: '', operation_filter: '', feedback_type: '', order_id: '', search: '' })
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
      operation_filter: filters.operation_filter || undefined,
      feedback_type: filters.feedback_type || undefined,
      order_id: filters.order_id || undefined,
      search: filters.search || undefined,
      page: page.value,
      limit: limit.value,
    })
    tickets.value = data.items
    total.value = data.total
  } catch (e) {
    error.value = formatApiError(e, '反馈工单加载失败。')
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
    error.value = formatApiError(e, '反馈工单保存失败。')
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
    error.value = formatApiError(e, `反馈工单状态更新失败：${status}。`)
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
  filters.operation_filter = routeText(route.query.operation_filter)
  filters.feedback_type = routeText(route.query.feedback_type)
  filters.order_id = routeText(route.query.order_id)
  filters.search = routeText(route.query.search)
}

function routeFilterSnapshot() {
  return [
    routeText(route.query.status),
    routeText(route.query.priority),
    routeText(route.query.operation_filter),
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
