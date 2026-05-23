<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <span class="font-medium text-slate-800">活动日志</span>
    </template>
    <div v-if="rows.length === 0" class="text-sm text-slate-500">暂无记录</div>
    <el-timeline v-else>
      <el-timeline-item v-for="a in rows" :key="a.id" :timestamp="formatTime(a.created_at)" placement="top">
        <div class="text-sm font-medium text-slate-800">{{ a.action }}</div>
        <pre v-if="a.diff" class="mt-1 max-h-40 overflow-auto rounded bg-slate-50 p-2 text-xs text-slate-600">{{
          JSON.stringify(a.diff, null, 2)
        }}</pre>
      </el-timeline-item>
    </el-timeline>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import type { ObjectType } from '@/constants/objectType'
import * as objApi from '@/api/objects'

const props = defineProps<{ objectType: ObjectType; objectId: string }>()

const loading = ref(false)
const rows = ref<objApi.ActivityRow[]>([])

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

async function load() {
  loading.value = true
  try {
    const page = await objApi.listActivity(props.objectType, props.objectId, 1, 80)
    rows.value = page.items
  } finally {
    loading.value = false
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
