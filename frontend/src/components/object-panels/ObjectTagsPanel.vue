<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <span class="font-medium text-slate-800">标签</span>
        <div class="flex flex-wrap items-center gap-2">
          <el-select v-model="selectedTag" placeholder="选择已有标签" clearable filterable style="width: 200px" size="small">
            <el-option v-for="t in allTags" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
          <el-button type="primary" size="small" :disabled="!selectedTag" @click="attach">挂载</el-button>
          <el-button size="small" @click="showNew = true">新建标签</el-button>
        </div>
      </div>
    </template>
    <div v-if="attached.length === 0" class="text-sm text-slate-500">暂无标签</div>
    <div v-else class="flex flex-wrap gap-2">
      <el-tag
        v-for="x in attached"
        :key="x.object_tag_id"
        closable
        :color="x.tag.color || undefined"
        @close="detach(x.tag.id)"
      >
        {{ x.tag.name }}
      </el-tag>
    </div>
    <el-dialog v-model="showNew" title="新建标签" width="400px" @closed="resetNewTag">
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model="newTag.name" /></el-form-item>
        <el-form-item label="颜色（可选）"><el-input v-model="newTag.color" placeholder="#409EFF" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNew = false">取消</el-button>
        <el-button type="primary" :loading="savingTag" @click="createNewTag">创建</el-button>
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

const loading = ref(false)
const savingTag = ref(false)
const attached = ref<objApi.ObjectTagRow[]>([])
const allTags = ref<objApi.Tag[]>([])
const selectedTag = ref<string | undefined>(undefined)
const showNew = ref(false)
const newTag = reactive({ name: '', color: '' })

function resetNewTag() {
  newTag.name = ''
  newTag.color = ''
}

async function loadAttached() {
  loading.value = true
  try {
    const page = await objApi.listObjectTags(props.objectType, props.objectId, 1, 200)
    attached.value = page.items
  } finally {
    loading.value = false
  }
}

async function loadAllTags() {
  const page = await objApi.listTags(1, 500)
  allTags.value = page.items
}

async function attach() {
  if (!selectedTag.value) return
  await objApi.attachTag(props.objectType, props.objectId, selectedTag.value)
  selectedTag.value = undefined
  ElMessage.success('已挂载')
  await loadAttached()
}

async function detach(tagId: string) {
  await objApi.detachTag(props.objectType, props.objectId, tagId)
  ElMessage.success('已移除')
  await loadAttached()
}

async function createNewTag() {
  if (!newTag.name.trim()) {
    ElMessage.warning('请输入标签名')
    return
  }
  savingTag.value = true
  try {
    const t = await objApi.createTag(newTag.name.trim(), newTag.color.trim() || null)
    await objApi.attachTag(props.objectType, props.objectId, t.id)
    showNew.value = false
    ElMessage.success('已创建并挂载')
    await loadAllTags()
    await loadAttached()
  } finally {
    savingTag.value = false
  }
}

watch(
  () => [props.objectType, props.objectId] as const,
  () => {
    loadAttached()
  },
  { immediate: false },
)

onMounted(async () => {
  await loadAllTags()
  await loadAttached()
})
defineExpose({ reload: loadAttached })
</script>
