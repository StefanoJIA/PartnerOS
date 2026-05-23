<template>
  <div class="space-y-4">
    <div v-if="combined.length">
      <p v-if="title" class="mb-2 text-sm font-medium text-slate-700">{{ title }}</p>
      <ul class="space-y-2">
        <li
          v-for="(row, i) in combined"
          :key="row.lead_id + '-' + (row.timestamp || i)"
          class="flex flex-wrap items-start justify-between gap-2 rounded border border-slate-100 bg-white p-3 text-sm"
        >
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <span class="font-medium text-slate-800">{{ row.company_name }}</span>
              <el-tag size="small" :type="badgeType(row.badge)">{{ row.badge }}</el-tag>
            </div>
            <p class="mt-1 text-xs text-slate-500">
              {{ row.type }} · {{ row.channel }} · {{ formatTime(row.timestamp) }}
            </p>
            <p v-if="row.summary" class="mt-1 line-clamp-2 text-xs text-slate-600">{{ row.summary }}</p>
          </div>
          <router-link :to="{ path: '/lead-intelligence', query: { leadId: row.lead_id } }">
            <el-button size="small" type="primary" link>Open Lead</el-button>
          </router-link>
        </li>
      </ul>
    </div>
    <p v-else class="text-sm text-slate-500">{{ emptyText }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DailyOpsRecentActivity } from '@/api/dailyOps'
import { RECENT_ACTIVITY_EMPTY } from '@/constants/dailyOps'

const props = withDefaults(
  defineProps<{
    items?: DailyOpsRecentActivity[]
    title?: string
    emptyText?: string
  }>(),
  {
    items: () => [],
    emptyText: RECENT_ACTIVITY_EMPTY,
  },
)

const combined = computed(() => props.items ?? [])

function formatTime(iso: string | null | undefined): string {
  if (!iso) return 'Unknown time'
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return 'Unknown time'
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return 'Unknown time'
  }
}

function badgeType(badge: string): 'success' | 'warning' | 'info' | '' {
  if (badge === 'Manual sent') return 'success'
  if (badge === 'Contact research') return 'warning'
  if (badge === 'Follow-up scheduled') return 'info'
  return ''
}
</script>
