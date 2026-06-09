<template>
  <div class="space-y-4">
    <div>
      <h2 class="text-xl font-semibold text-slate-800">系统健康 / Portal 准备度</h2>
      <p class="mt-1 text-sm text-slate-600">
        面向外部看板的只读 Portal 集成状态。数据来自
        <code class="text-xs">/health</code>,
        <code class="text-xs">/api/v1/system/readiness</code>,
        <code class="text-xs">/api/v1/portal/manifest</code>,
        <code class="text-xs">/api/v1/portal/summary</code>, and
        <code class="text-xs">/api/v1/portal/a-domain/status</code>。不会展示密钥。
      </p>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb-1"
      title="只读 Portal 集成"
      description="不自动发送。客户开发只允许人工审查。intelliOffice 不抓取 LinkedIn，也不自动执行平台动作。"
    />

    <div class="flex flex-wrap gap-2">
      <router-link to="/portal-consumer-mock">
        <el-button size="small" type="primary" plain>外部 Portal 消费端模拟</el-button>
      </router-link>
    </div>

    <SystemStatusPanel :compact="false" :show-detail-link="false" />

    <el-card v-loading="portalLoading" shadow="never">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <span class="font-medium text-slate-800">Portal 准备度</span>
          <el-tag size="small" type="info" effect="plain">只读</el-tag>
        </div>
      </template>

      <el-alert v-if="portalError" type="warning" :closable="false" show-icon class="mb-3" :title="portalError" />

      <template v-else-if="portalSummary?.data">
        <dl class="grid gap-3 text-sm md:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt class="text-slate-500">服务</dt>
            <dd class="font-medium">{{ portalSummary.data.service_id }} · {{ portalSummary.data.service_name }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">运行模式</dt>
            <dd>{{ portalSummary.data.runtime_mode || '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">API version</dt>
            <dd>{{ portalSummary.data.api_version || '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">线索总数</dt>
            <dd class="font-semibold">{{ portalSummary.data.lead_intelligence?.total_leads ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">高优先级</dt>
            <dd class="font-semibold text-rose-700">{{ portalSummary.data.lead_intelligence?.high_priority ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">等待回复</dt>
            <dd>{{ portalSummary.data.lead_intelligence?.waiting_for_reply ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">待首次触达</dt>
            <dd>{{ portalSummary.data.lead_intelligence?.needs_first_outreach ?? '—' }}</dd>
          </div>
          <div>
            <dt class="text-slate-500">人工触达准备</dt>
            <dd>
              <el-tag size="small" :type="aDomainStatus?.data?.manual_outreach_ready ? 'success' : 'warning'">
                {{ aDomainStatus?.data?.manual_outreach_ready ? '是' : '否' }}
              </el-tag>
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">自动发送</dt>
            <dd>
              <el-tag size="small" type="success" effect="plain">已禁用</el-tag>
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">Portal summary endpoint</dt>
            <dd>
              <el-tag size="small" :type="summaryEndpointOk ? 'success' : 'danger'">
                {{ summaryEndpointOk ? '正常' : '错误' }}
              </el-tag>
            </dd>
          </div>
        </dl>

        <p v-if="aDomainStatus?.data?.latest_stage" class="mt-3 text-xs text-slate-500">
          A-domain stage: {{ aDomainStatus.data.latest_stage }}
          · daily workflow {{ aDomainStatus.data.daily_workflow_ready ? '就绪' : '未就绪' }}
        </p>
      </template>
    </el-card>

    <el-card v-if="manifestModules.length" shadow="never">
      <template #header>Portal 模块（只读）</template>
      <el-table :data="manifestModules" size="small" stripe>
        <el-table-column prop="key" label="Key" width="160" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="frontend_route" label="路由" />
      </el-table>
    </el-card>

    <el-card v-if="capabilities.length" shadow="never">
      <template #header>能力</template>
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
    portalError.value = 'Portal 摘要加载失败，请确认 backend 是否运行。'
    console.error(e)
  } finally {
    portalLoading.value = false
  }
}

onMounted(loadPortalData)
</script>
