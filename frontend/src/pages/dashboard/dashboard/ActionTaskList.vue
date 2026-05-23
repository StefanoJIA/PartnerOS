<template>
  <ul v-if="items?.length" class="space-y-1 text-sm">
    <li v-for="t in items" :key="t.id" class="flex flex-wrap items-center gap-2">
      <el-button link type="primary" @click="$emit('go', t.id)">{{ t.title }}</el-button>
      <span class="text-slate-400">{{ t.due_at ? new Date(t.due_at).toLocaleString() : '' }}</span>
    </li>
  </ul>
  <p v-else class="text-sm text-slate-500">暂无</p>
</template>

<script setup lang="ts">
import type { TaskActionBrief } from '@/api/dashboard'

defineProps<{ items: TaskActionBrief[] | undefined }>()
defineEmits<{ go: [id: string] }>()
</script>
