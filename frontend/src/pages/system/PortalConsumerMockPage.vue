<template>
  <div class="space-y-4">
    <div>
      <h2 class="text-xl font-semibold text-slate-800">External Portal Consumer Mock</h2>
      <p class="mt-1 text-sm text-slate-600">
        This mock simulates how a future unified Portal can read intelliOffice status. It is read-only.
      </p>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="Read-only portal integration"
      description="No automatic sending. Human-reviewed outreach only. This page only calls v1 portal and readiness endpoints — no write APIs, no secrets, no customer email lists."
    />

    <div class="flex gap-2">
      <el-button size="small" type="primary" :loading="loading" @click="load">Refresh</el-button>
      <router-link to="/system-health">
        <el-button size="small" link>System health</el-button>
      </router-link>
    </div>

    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <template v-else-if="loaded">
      <el-card shadow="never">
        <template #header>Service identity</template>
        <dl class="grid gap-3 text-sm md:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt class="text-slate-500">service_id</dt>
            <dd class="font-medium">{{ summary?.service_id || manifest?.service_id || '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">runtime_mode</dt>
            <dd>{{ summary?.runtime_mode || manifest?.runtime_mode || '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">api_version</dt>
            <dd>{{ summary?.api_version || manifest?.api_version || '—' }}</dd>
          </div>
        </dl>
      </el-card>

      <el-card shadow="never">
        <template #header>Health &amp; readiness</template>
        <dl class="grid gap-3 text-sm md:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt class="text-slate-500">health status</dt>
            <dd>
              <el-tag size="small" :type="summary?.health?.status === 'ok' ? 'success' : 'warning'">
                {{ summary?.health?.status || '—' }}
              </el-tag>
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">database_status</dt>
            <dd>{{ summary?.health?.database_status || readiness?.database_status || '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">migration_pending</dt>
            <dd>{{ formatBool(summary?.health?.migration_pending) }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">readiness ok</dt>
            <dd>{{ formatBool(readiness?.ok) }}</dd>
          </div>
        </dl>
      </el-card>

      <el-card shadow="never">
        <template #header>Daily lead intelligence (aggregated counts only)</template>
        <dl class="grid gap-3 text-sm md:grid-cols-2 lg:grid-cols-4">
          <div>
            <dt class="text-slate-500">total leads</dt>
            <dd class="text-lg font-semibold">{{ li?.total_leads ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">high priority</dt>
            <dd class="text-lg font-semibold text-rose-700">{{ li?.high_priority ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">waiting reply</dt>
            <dd>{{ li?.waiting_for_reply ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">needs first outreach</dt>
            <dd>{{ li?.needs_first_outreach ?? '—' }}</dd>
          </div>
        </dl>
      </el-card>

      <el-card shadow="never">
        <template #header>Outreach safety flags</template>
        <dl class="grid gap-3 text-sm md:grid-cols-2">
          <div>
            <dt class="text-slate-500">manual_outreach_ready</dt>
            <dd>
              <el-tag size="small" :type="aDomain?.manual_outreach_ready ? 'success' : 'warning'">
                {{ formatBool(aDomain?.manual_outreach_ready) }}
              </el-tag>
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">automatic_sending_enabled</dt>
            <dd>
              <el-tag size="small" type="success" effect="plain">false (disabled)</el-tag>
            </dd>
          </div>
        </dl>
      </el-card>

      <el-card v-if="capabilities.length" shadow="never">
        <template #header>Capabilities</template>
        <div class="flex flex-wrap gap-1">
          <el-tag v-for="c in capabilities" :key="c" size="small" effect="plain">{{ c }}</el-tag>
        </div>
      </el-card>

      <el-card v-if="warnings.length" shadow="never">
        <template #header>Warnings</template>
        <ul class="list-disc space-y-1 pl-5 text-sm text-amber-800">
          <li v-for="(w, i) in warnings" :key="i">{{ w }}</li>
        </ul>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  fetchADomainStatus,
  fetchPortalManifest,
  fetchPortalSummary,
  fetchSystemReadiness,
} from '@/api/system'
import { formatApiError } from '@/api/errors'

const loading = ref(false)
const error = ref('')
const loaded = ref(false)

const manifest = ref<Record<string, unknown> | null>(null)
const summary = ref<Record<string, unknown> | null>(null)
const aDomain = ref<Record<string, unknown> | null>(null)
const readiness = ref<Record<string, unknown> | null>(null)

const li = computed(() => summary.value?.lead_intelligence as Record<string, number> | undefined)
const capabilities = computed(() => {
  const fromSummary = (summary.value?.capabilities as string[]) || []
  const fromManifest = (manifest.value?.capabilities as string[]) || []
  return fromSummary.length ? fromSummary : fromManifest
})
const warnings = computed(() => {
  const sw = (summary.value?.warnings as string[]) || []
  const rw = (readiness.value?.warnings as string[]) || []
  return [...sw, ...rw.filter((w) => !sw.includes(w))]
})

function formatBool(v: boolean | undefined): string {
  if (v === true) return 'true'
  if (v === false) return 'false'
  return '—'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [m, s, a, r] = await Promise.all([
      fetchPortalManifest(),
      fetchPortalSummary(),
      fetchADomainStatus(),
      fetchSystemReadiness(),
    ])
    if (a.data?.automatic_sending_enabled !== false) {
      throw new Error('Unexpected: automatic_sending_enabled is not false')
    }
    manifest.value = m.data as Record<string, unknown>
    summary.value = s.data as Record<string, unknown>
    aDomain.value = a.data as Record<string, unknown>
    readiness.value = r.data as Record<string, unknown>
    loaded.value = true
  } catch (e: unknown) {
    error.value = formatApiError(
      e,
      'Failed to load portal consumer data. Ensure backend is running and v1 portal endpoints are available.',
    )
    loaded.value = false
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
