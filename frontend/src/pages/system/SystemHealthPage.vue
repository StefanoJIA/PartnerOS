<template>
  <div class="space-y-4">
    <div>
      <h2 class="text-xl font-semibold text-slate-800">System Health · Portal Readiness</h2>
      <p class="mt-1 text-sm text-slate-600">
        Read-only portal integration for external dashboards. Data from
        <code class="text-xs">/health</code>,
        <code class="text-xs">/api/v1/system/readiness</code>,
        <code class="text-xs">/api/v1/portal/manifest</code>,
        <code class="text-xs">/api/v1/portal/summary</code>, and
        <code class="text-xs">/api/v1/portal/a-domain/status</code>. No secrets are shown.
      </p>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb-1"
      title="Read-only portal integration"
      description="No automatic sending. Human-reviewed outreach only. intelliOffice does not scrape LinkedIn or automate platform actions."
    />

    <SystemStatusPanel :compact="false" :show-detail-link="false" />

    <el-card v-loading="portalLoading" shadow="never">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <span class="font-medium text-slate-800">Portal Readiness</span>
          <el-tag size="small" type="info" effect="plain">Read-only</el-tag>
        </div>
      </template>

      <el-alert v-if="portalError" type="warning" :closable="false" show-icon class="mb-3" :title="portalError" />

      <template v-else-if="portalSummary?.data">
        <dl class="grid gap-3 text-sm md:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt class="text-slate-500">Service</dt>
            <dd class="font-medium">{{ portalSummary.data.service_id }} · {{ portalSummary.data.service_name }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">Runtime mode</dt>
            <dd>{{ portalSummary.data.runtime_mode || '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">API version</dt>
            <dd>{{ portalSummary.data.api_version || '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">Total leads</dt>
            <dd class="font-semibold">{{ portalSummary.data.lead_intelligence?.total_leads ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">High priority</dt>
            <dd class="font-semibold text-rose-700">{{ portalSummary.data.lead_intelligence?.high_priority ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">Waiting for reply</dt>
            <dd>{{ portalSummary.data.lead_intelligence?.waiting_for_reply ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">Needs first outreach</dt>
            <dd>{{ portalSummary.data.lead_intelligence?.needs_first_outreach ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">Manual outreach ready</dt>
            <dd>
              <el-tag size="small" :type="aDomainStatus?.data?.manual_outreach_ready ? 'success' : 'warning'">
                {{ aDomainStatus?.data?.manual_outreach_ready ? 'Yes' : 'No' }}
              </el-tag>
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">Automatic sending</dt>
            <dd>
              <el-tag size="small" type="success" effect="plain">Disabled</el-tag>
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">Portal summary endpoint</dt>
            <dd>
              <el-tag size="small" :type="summaryEndpointOk ? 'success' : 'danger'">
                {{ summaryEndpointOk ? 'OK' : 'Error' }}
              </el-tag>
            </dd>
          </div>
        </dl>

        <p v-if="aDomainStatus?.data?.latest_stage" class="mt-3 text-xs text-slate-500">
          A-domain stage: {{ aDomainStatus.data.latest_stage }}
          · daily workflow {{ aDomainStatus.data.daily_workflow_ready ? 'ready' : 'not ready' }}
        </p>
      </template>
    </el-card>

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
import { computed, onMounted, ref } from 'vue'
import SystemStatusPanel from '@/components/system/SystemStatusPanel.vue'
import {
  fetchADomainStatus,
  fetchPortalManifest,
  fetchPortalSummary,
  type ADomainStatusEnvelope,
  type PortalSummaryEnvelope,
} from '@/api/system'

const manifestModules = ref<{ key: string; name: string; frontend_route?: string }[]>([])
const capabilities = ref<string[]>([])
const portalSummary = ref<PortalSummaryEnvelope | null>(null)
const aDomainStatus = ref<ADomainStatusEnvelope | null>(null)
const portalLoading = ref(false)
const portalError = ref('')

const summaryEndpointOk = computed(() => portalSummary.value?.ok === true && !!portalSummary.value?.data?.lead_intelligence)

async function loadPortalData() {
  portalLoading.value = true
  portalError.value = ''
  try {
    const [m, s, a] = await Promise.all([fetchPortalManifest(), fetchPortalSummary(), fetchADomainStatus()])
    manifestModules.value = m.data.modules || []
    capabilities.value = m.data.capabilities || s.data.capabilities || []
    portalSummary.value = s
    aDomainStatus.value = a
  } catch (e: unknown) {
    portalError.value = 'Failed to load portal summary. Is the backend running?'
    console.error(e)
  } finally {
    portalLoading.value = false
  }
}

onMounted(loadPortalData)
</script>
