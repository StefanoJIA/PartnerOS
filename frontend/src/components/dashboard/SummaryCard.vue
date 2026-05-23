<template>
  <div
    class="rounded border border-slate-100 bg-slate-50 px-3 py-2"
    :class="toneClass"
  >
    <div class="text-xs text-slate-500">{{ label }}</div>
    <div class="text-xl font-semibold" :class="valueClass">{{ value }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value: number
  tone?: 'danger' | 'warning' | 'info' | 'primary'
}>()

const toneClass = computed(() => {
  if (props.tone === 'danger') return 'border-rose-100 bg-rose-50'
  if (props.tone === 'warning') return 'border-amber-100 bg-amber-50'
  if (props.tone === 'info') return 'border-sky-100 bg-sky-50'
  if (props.tone === 'primary') return 'border-indigo-100 bg-indigo-50'
  return ''
})

const valueClass = computed(() => {
  if (props.tone === 'danger') return 'text-rose-700'
  if (props.tone === 'warning') return 'text-amber-700'
  if (props.tone === 'info') return 'text-sky-700'
  if (props.tone === 'primary') return 'text-indigo-700'
  return 'text-slate-800'
})
</script>
