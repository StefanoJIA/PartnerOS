<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <span class="font-medium text-slate-800">任务（负责人 / 承办人：assignee）</span>
        <el-button type="primary" size="small" @click="dialog = true">新建</el-button>
      </div>
    </template>
    <div v-if="rows.length === 0" class="text-sm text-slate-500">暂无关联任务</div>
    <el-table v-else :data="rows" size="small" stripe>
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="status" label="状态" width="90" />
      <el-table-column prop="due_at" label="到期" width="170" />
      <el-table-column label="" width="100" align="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status !== 'done'"
            link
            type="primary"
            size="small"
            :loading="row._cp"
            @click="complete(row)"
          >
            完成
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="dialog" title="新建任务" width="480px" @closed="resetForm">
      <el-form label-position="top">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="到期（可选）"><el-date-picker v-model="due" type="datetime" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="create">创建</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive, watch } from 'vue'
import type { ObjectType } from '@/constants/objectType'
import * as objApi from '@/api/objects'
import { ElMessage } from 'element-plus'

const props = defineProps<{ objectType: ObjectType; objectId: string }>()

const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const rows = ref<(objApi.TaskRow & { _cp?: boolean })[]>([])
const due = ref<Date | null>(null)
const form = reactive({ title: '' })

function resetForm() {
  form.title = ''
  due.value = null
}

async function load() {
  loading.value = true
  try {
    const page = await objApi.listObjectTasks(props.objectType, props.objectId, 1, 100, null)
    rows.value = page.items.map((i) => ({ ...i }))
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  saving.value = true
  try {
    await objApi.createTask({
      title: form.title.trim(),
      related_object_type: props.objectType,
      related_object_id: props.objectId,
      due_at: due.value ? due.value.toISOString() : null,
    })
    dialog.value = false
    ElMessage.success('已创建')
    await load()
  } finally {
    saving.value = false
  }
}

async function complete(row: objApi.TaskRow & { _cp?: boolean }) {
  row._cp = true
  try {
    await objApi.completeTask(row.id)
    ElMessage.success('已完成')
    await load()
  } finally {
    row._cp = false
  }
}

watch(
  () => [props.objectType, props.objectId] as const,
  () => load(),
  { immediate: false },
)

onMounted(load)
defineExpose({ reload: load })
</script>
