<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-800">任务中心</h2>
      <el-button type="primary" @click="openCreate">新建任务</el-button>
    </div>

    <el-row :gutter="12">
      <el-col :xs="24" :sm="8" :md="4" v-for="c in statCards" :key="c.label">
        <el-card shadow="hover" class="!rounded-lg">
          <div class="text-xs text-slate-500">{{ c.label }}</div>
          <div class="text-2xl font-semibold text-slate-800">{{ c.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <el-form :inline="true" class="flex flex-wrap items-end gap-2" @submit.prevent="load">
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width: 140px">
            <el-option v-for="s in TASK_STATUSES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" clearable placeholder="全部" style="width: 120px">
            <el-option v-for="p in PRIORITY_LEVELS" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联类型">
          <el-select v-model="filters.related_object_type" clearable placeholder="全部" filterable style="width: 160px">
            <el-option v-for="o in RELATED_OBJECT_TYPES" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="filters.assignee_user_id" clearable filterable placeholder="选择用户" style="width: 200px">
            <el-option v-for="u in users" :key="u.id" :label="`${u.full_name} (${u.email})`" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="到期自">
          <el-date-picker v-model="filters.due_from" type="datetime" style="width: 100%" />
        </el-form-item>
        <el-form-item label="到">
          <el-date-picker v-model="filters.due_to" type="datetime" style="width: 100%" />
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filters.search" clearable placeholder="标题/描述" style="width: 160px" />
        </el-form-item>
        <el-form-item label="排序">
          <el-select v-model="filters.sort" style="width: 160px">
            <el-option label="到期 ↑" value="due_at_asc" />
            <el-option label="到期 ↓" value="due_at_desc" />
            <el-option label="优先级 ↓" value="priority_desc" />
            <el-option label="创建 ↓" value="created_at_desc" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="filters.overdue">仅逾期</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="filters.due_today">今日到期</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="filters.this_week">本周到期</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">筛选</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="rows" v-loading="loading" stripe size="small" class="mt-2">
        <template #empty>
          <el-empty description="无匹配任务" />
        </template>
        <el-table-column prop="title" label="标题" min-width="160" />
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column prop="priority" label="优先级" width="80" />
        <el-table-column label="Owner / Assigned" min-width="140">
          <template #default="{ row }">
            <span class="text-xs">{{ row.assignee_email || row.assignee_user_id || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="到期" width="118">
          <template #default="{ row }">
            <div v-if="row.due_at">
              <el-tag v-if="isDueToday(row)" type="warning" size="small">今日</el-tag>
              <span :class="rowClass(row)">{{ fmtDate(row.due_at) }}</span>
            </div>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="关联对象" min-width="120">
          <template #default="{ row }">
            <span v-if="row.related_object_type" class="text-xs">
              {{ row.related_object_type }}<br /><span class="text-slate-400">{{ row.related_object_id }}</span>
            </span>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="创建" width="110">
          <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="完成于" width="110">
          <template #default="{ row }">
            <span v-if="row.status === 'done'">{{ row.completed_at ? fmtDate(row.completed_at) : '—' }}</span>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openRelated(row)">打开关联</el-button>
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button
              v-if="row.status !== 'done'"
              link
              type="success"
              size="small"
              @click="doComplete(row)"
            >完成</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dlg.visible" :title="dlg.id ? '编辑任务' : '新建任务'" width="520px" @closed="resetDlg">
      <el-form label-position="top">
        <el-form-item label="标题" required><el-input v-model="dlg.form.title" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="dlg.form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="dlg.form.status" style="width: 100%">
            <el-option v-for="s in TASK_STATUSES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="dlg.form.priority" clearable style="width: 100%">
            <el-option v-for="p in PRIORITY_LEVELS" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人 (assignee_user_id)">
          <el-select v-model="dlg.form.assignee_user_id" clearable filterable style="width: 100%">
            <el-option v-for="u in users" :key="u.id" :label="`${u.full_name}`" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联 object_type">
          <el-select v-model="dlg.form.related_object_type" clearable filterable placeholder="可选" style="width: 100%">
            <el-option v-for="o in RELATED_OBJECT_TYPES" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联 object_id (UUID)">
          <el-input v-model="dlg.form.related_object_id" />
        </el-form-item>
        <el-form-item label="到期时间">
          <el-date-picker v-model="dlg.due" type="datetime" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg.visible = false">取消</el-button>
        <el-button type="primary" :loading="dlg.saving" @click="saveDlg">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as taskApi from '@/api/tasks'
import type { TaskDto } from '@/api/tasks'
import { PRIORITY_LEVELS, TASK_STATUSES } from '@/constants/statusEnums'
import { ElMessage } from 'element-plus'

const RELATED_OBJECT_TYPES = [
  { value: 'lead', label: 'lead' },
  { value: 'company', label: 'company' },
  { value: 'contact', label: 'contact' },
  { value: 'rfq', label: 'rfq' },
  { value: 'sample', label: 'sample' },
  { value: 'order', label: 'order' },
  { value: 'manufacturing_partner', label: 'manufacturing_partner' },
  { value: 'product', label: 'product' },
] as const

const router = useRouter()
const loading = ref(false)
const stats = ref<taskApi.TaskStats | null>(null)
const rows = ref<TaskDto[]>([])
const users = ref<taskApi.UserBrief[]>([])

const filters = reactive({
  status: '' as string,
  priority: '' as string,
  related_object_type: '' as string,
  assignee_user_id: '' as string,
  due_from: null as Date | null,
  due_to: null as Date | null,
  search: '' as string,
  sort: 'due_at_asc',
  overdue: false,
  due_today: false,
  this_week: false,
})

const statCards = computed(() => [
  { label: '今日到期', value: stats.value?.due_today ?? '—' },
  { label: '逾期', value: stats.value?.overdue ?? '—' },
  { label: '本周', value: stats.value?.this_week ?? '—' },
  { label: '未完成', value: stats.value?.open_tasks ?? '—' },
  { label: '已完成', value: stats.value?.completed_tasks ?? '—' },
])

const dlg = reactive({
  visible: false,
  id: '' as string,
  saving: false,
  due: null as Date | null,
  form: {
    title: '',
    description: '' as string | null,
    status: 'open',
    priority: '' as string | null,
    assignee_user_id: '' as string,
    related_object_type: '' as string,
    related_object_id: '' as string,
  },
})

function fmtDate(iso: string) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function nowUtcMs() {
  return Date.now()
}

function isDueToday(row: TaskDto) {
  if (!row.due_at || row.status === 'done') return false
  const d = new Date(row.due_at)
  const t = new Date()
  return d.getUTCFullYear() === t.getUTCFullYear() && d.getUTCMonth() === t.getUTCMonth() && d.getUTCDate() === t.getUTCDate()
}

function isOverdue(row: TaskDto) {
  if (!row.due_at || row.status === 'done') return false
  return new Date(row.due_at).getTime() < nowUtcMs()
}

function rowClass(row: TaskDto) {
  if (row.status === 'done') return ''
  return isOverdue(row) ? 'text-red-600 font-medium' : ''
}

async function loadUsers() {
  const page = await taskApi.listUsersBrief(1, 200)
  users.value = page.items
}

async function loadStats() {
  stats.value = await taskApi.fetchTaskStats()
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: 1,
      limit: 100,
      sort: filters.sort,
    }
    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    if (filters.related_object_type) params.related_object_type = filters.related_object_type
    if (filters.assignee_user_id) params.assignee_user_id = filters.assignee_user_id
    if (filters.due_from) params.due_from = filters.due_from.toISOString()
    if (filters.due_to) params.due_to = filters.due_to.toISOString()
    if (filters.search) params.search = filters.search
    if (filters.overdue) params.overdue = true
    if (filters.due_today) params.due_today = true
    if (filters.this_week) params.this_week = true
    const page = await taskApi.fetchTasks(params)
    rows.value = page.items
    await loadStats()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dlg.id = ''
  resetDlg()
  dlg.visible = true
}

function openEdit(row: TaskDto) {
  dlg.id = row.id
  dlg.form.title = row.title
  dlg.form.description = row.description
  dlg.form.status = row.status
  dlg.form.priority = row.priority
  dlg.form.assignee_user_id = row.assignee_user_id || ''
  dlg.form.related_object_type = row.related_object_type || ''
  dlg.form.related_object_id = row.related_object_id || ''
  dlg.due = row.due_at ? new Date(row.due_at) : null
  dlg.visible = true
}

function resetDlg() {
  dlg.form.title = ''
  dlg.form.description = ''
  dlg.form.status = 'open'
  dlg.form.priority = ''
  dlg.form.assignee_user_id = ''
  dlg.form.related_object_type = ''
  dlg.form.related_object_id = ''
  dlg.due = null
}

async function saveDlg() {
  if (!dlg.form.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  dlg.saving = true
  try {
    const body: Record<string, unknown> = {
      title: dlg.form.title.trim(),
      description: dlg.form.description || null,
      status: dlg.form.status,
      priority: dlg.form.priority || null,
      assignee_user_id: dlg.form.assignee_user_id || null,
      due_at: dlg.due ? dlg.due.toISOString() : null,
    }
    const rot = dlg.form.related_object_type?.trim()
    const rid = dlg.form.related_object_id?.trim()
    if (rot && rid) {
      body.related_object_type = rot
      body.related_object_id = rid
    } else {
      body.related_object_type = null
      body.related_object_id = null
    }
    if (dlg.id) await taskApi.updateTask(dlg.id, body)
    else await taskApi.createTask(body)
    dlg.visible = false
    ElMessage.success('已保存')
    await load()
  } finally {
    dlg.saving = false
  }
}

async function doComplete(row: TaskDto) {
  await taskApi.completeTask(row.id)
  ElMessage.success('已完成')
  await load()
}

function openRelated(row: TaskDto) {
  const t = row.related_object_type
  const id = row.related_object_id
  if (!t || !id) {
    ElMessage.info('无关联对象')
    return
  }
  if (t === 'lead') router.push({ name: 'lead-detail', params: { leadId: id } })
  else if (t === 'rfq') router.push({ name: 'rfq-detail', params: { rfqId: id } })
  else if (t === 'sample') router.push({ name: 'sample-detail', params: { sampleId: id } })
  else if (t === 'order') router.push({ name: 'order-detail', params: { orderId: id } })
  else if (t === 'company') router.push({ name: 'company-detail', params: { companyId: id } })
  else if (t === 'contact') router.push({ name: 'contact-detail', params: { contactId: id } })
  else if (t === 'manufacturing_partner') router.push({ name: 'partner-detail', params: { partnerId: id } })
  else if (t === 'product') router.push({ name: 'product-detail', params: { productId: id } })
  else ElMessage.info(`请从列表中找到 ${t}`)
}

onMounted(async () => {
  await loadUsers()
  await load()
})
</script>
