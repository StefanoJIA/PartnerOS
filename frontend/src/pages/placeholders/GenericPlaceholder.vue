<template>
  <div>
    <h2 class="text-xl font-semibold text-slate-800">{{ title }}</h2>
    <p class="mt-2 text-sm text-slate-600">This screen is a placeholder — extend with full CRUD as needed.</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string }>()
</script>
