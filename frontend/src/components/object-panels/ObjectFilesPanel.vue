<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <span class="font-medium text-slate-800">附件</span>
        <el-upload :show-file-list="false" :http-request="onPick">
          <template #trigger>
            <el-button type="primary" size="small" :loading="uploading">上传并挂载</el-button>
          </template>
        </el-upload>
      </div>
    </template>
    <div v-if="rows.length === 0" class="text-sm text-slate-500">暂无附件</div>
    <el-table v-else :data="rows" size="small" stripe>
      <el-table-column label="文件">
        <template #default="{ row }">{{ row.file.original_filename }}</template>
      </el-table-column>
      <el-table-column prop="purpose" label="用途" width="120" />
      <el-table-column label="" width="100" align="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" :loading="row._dl" @click="download(row)">下载</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import type { ObjectType } from '@/constants/objectType'
import type { UploadRequestOptions } from 'element-plus'
import * as objApi from '@/api/objects'
import { ElMessage } from 'element-plus'

const props = defineProps<{ objectType: ObjectType; objectId: string }>()

const loading = ref(false)
const uploading = ref(false)
const rows = ref<(objApi.FileAttachmentRow & { _dl?: boolean })[]>([])

async function load() {
  loading.value = true
  try {
    const page = await objApi.listObjectFiles(props.objectType, props.objectId, 1, 100)
    rows.value = page.items.map((i) => ({ ...i }))
  } finally {
    loading.value = false
  }
}

async function onPick(opt: UploadRequestOptions) {
  const raw = opt.file as File
  uploading.value = true
  try {
    const meta = await objApi.uploadFile(raw)
    await objApi.attachUploadedFile(meta.id, props.objectType, props.objectId, null)
    ElMessage.success('已挂载')
    await load()
    opt.onSuccess?.({} as never)
  } catch {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

async function download(row: objApi.FileAttachmentRow & { _dl?: boolean }) {
  row._dl = true
  try {
    const blob = await objApi.downloadFileBlob(row.file_id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = row.file.original_filename || 'download'
    a.click()
    window.URL.revokeObjectURL(url)
  } finally {
    row._dl = false
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
