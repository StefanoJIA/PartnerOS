<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <span class="font-medium text-slate-800">互动记录</span>
        <el-button type="primary" size="small" @click="dialog = true">记录互动</el-button>
      </div>
    </template>
    <div v-if="rows.length === 0" class="text-sm text-slate-500">暂无互动</div>
    <el-table v-else :data="rows" size="small" stripe>
      <el-table-column prop="interaction_date" label="时间" width="170" />
      <el-table-column prop="channel" label="渠道" width="90" />
      <el-table-column prop="interaction_type" label="类型" width="120" />
      <el-table-column label="" width="120" align="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" :loading="row._sp" @click="spawn(row)">生成任务</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="dialog" title="记录互动" width="520px" @closed="resetForm">
      <el-form label-position="top">
        <el-form-item label="类型"><el-input v-model="form.interaction_type" placeholder="call / email / meeting" /></el-form-item>
        <el-form-item label="渠道"><el-input v-model="form.channel" placeholder="phone / linkedin / in_person" /></el-form-item>
        <el-form-item label="主题"><el-input v-model="form.subject" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import type { ObjectType } from '@/constants/objectType'
import * as objApi from '@/api/objects'
import { ElMessage } from 'element-plus'

const props = defineProps<{ objectType: ObjectType; objectId: string }>()

const emit = defineEmits<{ 'task-spawned': [] }>()

const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const rows = ref<(objApi.InteractionRow & { _sp?: boolean })[]>([])
const form = reactive({
  interaction_type: 'note',
  channel: 'crm',
  subject: '',
  content: '',
})

function resetForm() {
  form.interaction_type = 'note'
  form.channel = 'crm'
  form.subject = ''
  form.content = ''
}

async function load() {
  loading.value = true
  try {
    const page = await objApi.listObjectInteractions(props.objectType, props.objectId, 1, 100)
    rows.value = page.items.map((i) => ({ ...i }))
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!form.interaction_type.trim() || !form.channel.trim()) {
    ElMessage.warning('请填写类型与渠道')
    return
  }
  saving.value = true
  try {
    await objApi.createInteraction({
      related_object_type: props.objectType,
      related_object_id: props.objectId,
      interaction_type: form.interaction_type.trim(),
      channel: form.channel.trim(),
      subject: form.subject.trim() || null,
      content: form.content.trim() || null,
    })
    dialog.value = false
    ElMessage.success('已保存')
    await load()
  } finally {
    saving.value = false
  }
}

async function spawn(row: objApi.InteractionRow & { _sp?: boolean }) {
  row._sp = true
  try {
    await objApi.spawnTaskFromInteraction(row.id, {})
    ElMessage.success('已从互动创建任务')
    emit('task-spawned')
  } finally {
    row._sp = false
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
