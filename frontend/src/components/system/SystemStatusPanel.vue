<template>
  <el-card shadow="never" v-loading="loading">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <span class="font-medium text-slate-800">System Status · Portal Readiness</span>
        <div class="flex gap-2">
          <el-button size="small" @click="load">Refresh</el-button>
          <router-link v-if="showDetailLink" to="/system-health">
            <el-button size="small" type="primary" link>Details</el-button>
          </router-link>
        </div>
      </div>
    </template>

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />

    <template v-else-if="health">
      <div class="mb-3 flex flex-wrap items-center gap-2">
        <el-tag :type="healthTagType" effect="dark">{{ healthLabel }}</el-tag>
        <el-tag v-if="health.runtime_mode" type="info" effect="plain">{{ health.runtime_mode }}</el-tag>
        <span class="text-xs text-slate-500">v{{ health.version || '—' }}</span>
      </div>

      <dl class="grid gap-2 text-sm md:grid-cols-2">
        <div><dt class="text-slate-500">Database</dt><dd>{{ health.database_status || '—' }}</dd></div>
        <div><dt class="text-slate-500">Lifecycle</dt><dd>{{ health.database_lifecycle_phase || '—' }}</dd></div>
        <div>
          <dt class="text-slate-500">Migration pending</dt>
          <dd>{{ health.migration_pending ? 'Yes' : 'No' }}</dd>
        </div>
        <div>
          <dt class="text-slate-500">Alembic</dt>
          <dd class="text-xs">{{ health.alembic_current_revision || '—' }} / {{ health.alembic_head_revision || '—' }}</dd>
        </div>
      </dl>

      <template v-if="readiness?.data">
        <el-divider class="my-3" />
        <p class="mb-2 text-xs font-medium text-slate-600">Readiness (v1)</p>
        <div class="flex flex-wrap gap-2 text-xs">
          <el-tag :type="readiness.data.database_ready ? 'success' : 'warning'" size="small">
            DB {{ readiness.data.database_ready ? 'ready' : 'not ready' }}
          </el-tag>
          <el-tag :type="readiness.data.redis_ready ? 'success' : 'info'" size="small">
            Redis {{ readiness.data.redis_ready ? 'ready' : 'optional off' }}
          </el-tag>
          <el-tag :type="readiness.data.worker_ready ? 'success' : 'info'" size="small">
            Worker {{ readiness.data.worker_ready ? 'ready' : 'optional off' }}
          </el-tag>
        </div>
        <ul v-if="readiness.data.warnings?.length" class="mt-2 list-disc pl-5 text-xs text-amber-700">
          <li v-for="(w, i) in readiness.data.warnings" :key="i">{{ w }}</li>
        </ul>
      </template>

      <template v-if="manifest?.data">
        <el-divider class="my-3" />
        <p class="mb-1 text-xs text-slate-600">
          <span class="font-medium">{{ manifest.data.service_name || manifest.data.service_id }}</span>
          · API {{ manifest.data.api_version || '—' }}
          · {{ (manifest.data.modules || []).length }} modules
        </p>
        <p class="text-xs text-slate-500 line-clamp-2">
          Capabilities: {{ (manifest.data.capabilities || []).slice(0, 8).join(', ') }}
          <span v-if="(manifest.data.capabilities || []).length > 8">…</span>
        </p>
      </template>

      <p v-if="compact" class="mt-3 text-xs text-slate-400">
        Dev frontend port is shown in the Vite terminal (often 5173 or 5174).
      </p>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  fetchLegacyHealth,
  fetchPortalManifest,
  fetchSystemReadiness,
  type LegacyHealth,
  type ManifestEnvelope,
  type ReadinessEnvelope,
} from '@/api/system'

withDefaults(defineProps<{ compact?: boolean; showDetailLink?: boolean }>(), {
  compact: true,
  showDetailLink: true,
})

const loading = ref(false)
const error = ref('')
const health = ref<LegacyHealth | null>(null)
const readiness = ref<ReadinessEnvelope | null>(null)
const manifest = ref<ManifestEnvelope | null>(null)

const healthLabel = computed(() => {
  const s = health.value?.status
  if (s === 'ok') return 'OK'
  if (s === 'degraded') return 'Degraded'
  return s || 'Unknown'
})

const healthTagType = computed(() => {
  const s = health.value?.status
  if (s === 'ok') return 'success'
  if (s === 'degraded') return 'warning'
  return 'danger'
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [h, r, m] = await Promise.all([
      fetchLegacyHealth(),
      fetchSystemReadiness(),
      fetchPortalManifest(),
    ])
    health.value = h
    readiness.value = r
    manifest.value = m
  } catch (e: unknown) {
    error.value = 'Failed to load system status. Is the backend running on :8000?'
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)

defineExpose({ load })
</script>
