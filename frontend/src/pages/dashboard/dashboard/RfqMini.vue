<template>
  <ul v-if="items?.length" class="space-y-1 text-sm">
    <li v-for="r in items" :key="r.id">
      <router-link :to="{ name: 'rfq-detail', params: { rfqId: r.id } }" class="text-blue-600 hover:underline">{{
        r.rfq_number
      }}</router-link>
      <span class="text-slate-400"> — {{ r.status }}</span>
    </li>
  </ul>
  <p v-else class="text-sm text-slate-500">暂无</p>
</template>

<script setup lang="ts">
defineProps<{ items: { id: string; rfq_number: string; status: string }[] | undefined }>()
</script>
