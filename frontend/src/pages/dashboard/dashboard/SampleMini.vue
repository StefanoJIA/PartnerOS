<template>
  <ul v-if="items?.length" class="space-y-1 text-sm">
    <li v-for="s in items" :key="s.id">
      <router-link :to="{ name: 'sample-detail', params: { sampleId: s.id } }" class="text-blue-600 hover:underline">
        {{ s.sample_request_number }}
      </router-link>
      <span class="text-slate-400"> — {{ s.sample_status }}</span>
    </li>
  </ul>
  <p v-else class="text-sm text-slate-500">暂无</p>
</template>

<script setup lang="ts">
defineProps<{ items: { id: string; sample_request_number: string; sample_status?: string }[] | undefined }>()
</script>
