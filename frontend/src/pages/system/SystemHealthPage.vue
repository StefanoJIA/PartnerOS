<template>
  <div class="space-y-4">
    <div>
      <h2 class="text-xl font-semibold text-slate-800">System Health · Portal Readiness</h2>
      <p class="mt-1 text-sm text-slate-600">
        Read-only view for internal MVP demos. Data from <code class="text-xs">/health</code>,
        <code class="text-xs">/api/v1/system/readiness</code>, and
        <code class="text-xs">/api/v1/portal/manifest</code>. No secrets are shown.
      </p>
    </div>

    <SystemStatusPanel :compact="false" :show-detail-link="false" />

    <el-card v-if="manifestModules.length" shadow="never">
      <template #header>Portal modules (read-only)</template>
      <el-table :data="manifestModules" size="small" stripe>
        <el-table-column prop="key" label="Key" width="160" />
        <el-table-column prop="name" label="Name" />
        <el-table-column prop="frontend_route" label="Route" />
      </el-table>
    </el-card>

    <el-card v-if="capabilities.length" shadow="never">
      <template #header>Capabilities</template>
      <div class="flex flex-wrap gap-1">
        <el-tag v-for="c in capabilities" :key="c" size="small" effect="plain">{{ c }}</el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import SystemStatusPanel from '@/components/system/SystemStatusPanel.vue'
import { fetchPortalManifest } from '@/api/system'

const manifestModules = ref<{ key: string; name: string; frontend_route?: string }[]>([])
const capabilities = ref<string[]>([])

onMounted(async () => {
  try {
    const m = await fetchPortalManifest()
    manifestModules.value = m.data.modules || []
    capabilities.value = m.data.capabilities || []
  } catch {
    manifestModules.value = []
    capabilities.value = []
  }
})
</script>
