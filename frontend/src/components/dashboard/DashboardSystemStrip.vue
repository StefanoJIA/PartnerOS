<template>
  <div v-loading="loading" class="rounded border border-slate-100 bg-slate-50 px-3 py-2 text-xs">
    <p class="mb-2 font-medium text-slate-600">System Status</p>
    <div v-if="error" class="text-rose-600">{{ error }}</div>
    <div v-else class="flex flex-wrap gap-2">
      <el-tag size="small" :type="backendOk ? 'success' : 'danger'">
        Backend {{ backendOk ? 'ok' : 'unreachable' }}
      </el-tag>
      <el-tag size="small" :type="dbReady ? 'success' : 'warning'">
        Database {{ dbReady ? 'ready' : 'not ready' }}
      </el-tag>
      <el-tag size="small" type="info">Portal read-only ok</el-tag>
      <el-tag size="small" type="success">Auto-send disabled</el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchLegacyHealth, fetchSystemReadiness } from '@/api/system'
import { BACKEND_HINT } from '@/api/errors'

const loading = ref(false)
const error = ref('')
const backendOk = ref(false)
const dbReady = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [health, readiness] = await Promise.all([fetchLegacyHealth(), fetchSystemReadiness()])
    backendOk.value = health.status === 'ok' || health.status === 'degraded'
    dbReady.value =
      health.database_status === 'ready' || readiness.data?.database_ready === true
  } catch {
    error.value = BACKEND_HINT
    backendOk.value = false
    dbReady.value = false
  } finally {
    loading.value = false
  }
}

onMounted(load)
defineExpose({ load })
</script>
