<template>
  <ul v-if="items?.length" class="space-y-1 text-sm">
    <li v-for="l in items" :key="l.id">
      <router-link class="text-blue-600 hover:underline" :to="{ name: 'lead-detail', params: { leadId: l.id } }">
        {{ l.lead_name }}
      </router-link>
      <span class="text-slate-400"> · {{ l.current_stage }}</span>
    </li>
  </ul>
  <p v-else class="text-sm text-slate-500">暂无</p>
</template>

<script setup lang="ts">
import type { LeadActionBrief } from '@/api/dashboard'

defineProps<{ items: LeadActionBrief[] | undefined }>()
</script>
