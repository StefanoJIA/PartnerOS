<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <span class="font-medium text-slate-800">备注</span>
        <el-button type="primary" size="small" @click="startCreate">新增</el-button>
      </div>
    </template>
    <div v-if="draft.active" class="mb-4 space-y-2 rounded border border-slate-200 p-3">
      <el-input v-model="draft.body" type="textarea" :rows="3" placeholder="备注内容" />
      <div class="flex gap-2">
        <el-button size="small" @click="cancelDraft">取消</el-button>
        <el-button type="primary" size="small" :loading="saving" @click="saveDraft">保存</el-button>
      </div>
    </div>
    <div v-if="rows.length === 0 && !draft.active" class="text-sm text-slate-500">暂无备注</div>
    <div v-else class="space-y-3">
      <div v-for="n in rows" :key="n.id" class="rounded border border-slate-100 bg-slate-50/80 p-3 text-sm">
        <div class="mb-2 flex items-start justify-between gap-2 text-xs text-slate-500">
          <span>{{ formatTime(n.created_at) }}</span>
          <span class="shrink-0 space-x-2">
            <el-button v-if="editingId !== n.id" link type="primary" size="small" @click="startEdit(n)">编辑</el-button>
            <el-button link type="danger" size="small" @click="remove(n)">删除</el-button>
          </span>
        </div>
        <template v-if="editingId === n.id">
          <el-input v-model="editBody" type="textarea" :rows="3" />
          <div class="mt-2 flex gap-2">
            <el-button size="small" @click="cancelEdit">取消</el-button>
            <el-button type="primary" size="small" :loading="saving" @click="saveEdit(n.id)">保存</el-button>
          </div>
        </template>
        <p v-else class="whitespace-pre-wrap text-slate-800">{{ n.body }}</p>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import type { ObjectType } from '@/constants/objectType'
import * as objApi from '@/api/objects'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps<{ objectType: ObjectType; objectId: string }>()

const loading = ref(false)
const saving = ref(false)
const rows = ref<objApi.Note[]>([])
const editingId = ref<string | null>(null)
const editBody = ref('')
const draft = reactive({ active: false, body: '' })

async function load() {
  loading.value = true
  try {
    const page = await objApi.listNotes(props.objectType, props.objectId, 1, 100)
    rows.value = page.items
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function startCreate() {
  draft.active = true
  draft.body = ''
  editingId.value = null
}

function cancelDraft() {
  draft.active = false
  draft.body = ''
}

async function saveDraft() {
  if (!draft.body.trim()) {
    ElMessage.warning('请输入备注内容')
    return
  }
  saving.value = true
  try {
    await objApi.createNote(props.objectType, props.objectId, draft.body.trim())
    draft.active = false
    ElMessage.success('已保存')
    await load()
  } finally {
    saving.value = false
  }
}

function startEdit(n: objApi.Note) {
  editingId.value = n.id
  editBody.value = n.body
  draft.active = false
}

function cancelEdit() {
  editingId.value = null
  editBody.value = ''
}

async function saveEdit(noteId: string) {
  if (!editBody.value.trim()) {
    ElMessage.warning('内容不能为空')
    return
  }
  saving.value = true
  try {
    await objApi.updateNote(props.objectType, props.objectId, noteId, editBody.value.trim())
    editingId.value = null
    ElMessage.success('已更新')
    await load()
  } finally {
    saving.value = false
  }
}

async function remove(n: objApi.Note) {
  await ElMessageBox.confirm('确定删除这条备注？', '确认', { type: 'warning' })
  await objApi.deleteNote(props.objectType, props.objectId, n.id)
  ElMessage.success('已删除')
  await load()
}

watch(
  () => [props.objectType, props.objectId] as const,
  () => load(),
  { immediate: false },
)

onMounted(load)
defineExpose({ reload: load })
</script>
