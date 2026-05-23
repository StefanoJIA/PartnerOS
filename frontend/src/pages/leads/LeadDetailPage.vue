<template>
  <div v-loading="loading" class="space-y-4">
    <div class="flex flex-wrap items-center gap-3">
      <el-button link type="primary" @click="$router.push({ name: 'leads' })">← 返回线索列表</el-button>
    </div>

    <template v-if="ws">
      <el-card shadow="never">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-slate-800">{{ ws.lead.lead_name }}</h2>
            <p class="mt-1 text-sm text-slate-600">
              阶段：{{ ws.lead.current_stage }} · 优先级：{{ ws.lead.priority || '—' }} · 负责人：{{ ws.owner_display || ws.lead.owner_user_id || '—' }}
            </p>
            <p class="mt-2 text-sm text-slate-700">
              来源：{{ ws.lead.source }} · 类型：{{ ws.lead.lead_type }} · 下一动作：{{ ws.lead.next_action || '—' }}
            </p>
            <p class="mt-1 text-sm text-slate-600">
              下次动作日：{{ ws.lead.next_action_due_date || '—' }} · 意向产品：{{ ws.lead.product_interest || '—' }}
            </p>
          </div>
          <div class="text-right text-sm text-slate-600">
            <div>公司：{{ ws.company.company_name }}</div>
            <div v-if="ws.contact">联系人：{{ ws.contact.first_name }} {{ ws.contact.last_name }}</div>
          </div>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>销售阶段（Pipeline）</template>
        <div class="flex flex-wrap gap-2">
          <el-button
            v-for="st in LEAD_PIPELINE_STAGES"
            :key="st"
            size="small"
            :type="ws.lead.current_stage === st ? 'primary' : 'default'"
            @click="setStage(st)"
          >
            {{ st }}
          </el-button>
        </div>
        <p class="mt-2 text-xs text-slate-500">点击阶段标签将调用 POST /leads/{id}/stage 并写入 activity log。</p>
      </el-card>

      <el-card shadow="never">
        <template #header>快捷动作</template>
        <div class="flex flex-wrap gap-2">
          <el-button size="small" type="success" @click="openIntelligenceWorkbench">A 域 · 情报工作台</el-button>
          <el-button size="small" @click="scrollTo('ai-panel')">LinkedIn / 跟进 / 邮件（AI）</el-button>
          <el-button size="small" @click="scrollTo('interaction-panel')">记录互动</el-button>
          <el-button size="small" @click="scrollTo('task-panel')">创建任务</el-button>
          <el-button size="small" type="primary" @click="quickRfq">创建 RFQ</el-button>
          <el-button size="small" type="primary" @click="quickSample">申请样品</el-button>
          <el-button size="small" @click="$router.push({ path: '/field-visits' })">地推拜访</el-button>
          <el-button size="small" @click="markDormant">标为 Dormant</el-button>
          <el-button size="small" @click="markStrategic">标为战略客户（公司）</el-button>
        </div>
      </el-card>

      <el-row :gutter="16">
        <el-col :xs="24" :lg="16">
          <el-card shadow="never" class="mb-4">
            <template #header>关联对象</template>
            <div class="space-y-4">
              <div>
                <div class="mb-1 text-sm font-medium text-slate-700">RFQ</div>
                <el-table v-if="ws.related_rfqs.length" :data="ws.related_rfqs" size="small" stripe>
                  <el-table-column label="#">
                    <template #default="{ row }">
                      <router-link class="text-blue-600" :to="{ name: 'rfq-detail', params: { rfqId: row.id } }">{{
                        row.rfq_number
                      }}</router-link>
                    </template>
                  </el-table-column>
                  <el-table-column prop="status" label="状态" />
                </el-table>
                <p v-else class="text-sm text-slate-500">暂无</p>
              </div>
              <div>
                <div class="mb-1 text-sm font-medium text-slate-700">样品</div>
                <el-table v-if="ws.related_samples.length" :data="ws.related_samples" size="small" stripe>
                  <el-table-column prop="sample_request_number" label="#" />
                  <el-table-column prop="sample_status" label="状态" />
                </el-table>
                <p v-else class="text-sm text-slate-500">暂无</p>
              </div>
              <div>
                <div class="mb-1 text-sm font-medium text-slate-700">订单</div>
                <el-table v-if="ws.related_orders.length" :data="ws.related_orders" size="small" stripe>
                  <el-table-column prop="order_number" label="#" />
                  <el-table-column prop="production_status" label="生产" />
                  <el-table-column prop="risk_level" label="风险" />
                </el-table>
                <p v-else class="text-sm text-slate-500">暂无</p>
              </div>
              <div>
                <div class="mb-1 text-sm font-medium text-slate-700">地推目标</div>
                <el-table v-if="ws.related_field_visits.length" :data="ws.related_field_visits" size="small" stripe>
                  <el-table-column prop="plan_name" label="计划" />
                  <el-table-column prop="status" label="状态" width="100" />
                  <el-table-column prop="scheduled_time" label="日程" />
                </el-table>
                <p v-else class="text-sm text-slate-500">暂无</p>
              </div>
            </div>
          </el-card>

          <div id="ai-panel">
            <ObjectAiActionsPanel
              object-type="lead"
              :object-id="leadId"
              variant="lead"
              :ai-context="aiContext"
            />
          </div>
          <div id="interaction-panel" class="mt-4">
            <ObjectInteractionsPanel object-type="lead" :object-id="leadId" @task-spawned="reloadWorkspace" />
          </div>
          <div id="task-panel" class="mt-4">
            <ObjectTasksPanel ref="tasksRef" object-type="lead" :object-id="leadId" />
          </div>
          <div class="mt-4 grid gap-4 lg:grid-cols-2">
            <ObjectNotesPanel ref="notesRef" object-type="lead" :object-id="leadId" />
            <ObjectTagsPanel ref="tagsRef" object-type="lead" :object-id="leadId" />
            <ObjectFilesPanel ref="filesRef" object-type="lead" :object-id="leadId" />
            <div class="lg:col-span-2">
              <ObjectActivityLogPanel ref="activityRef" object-type="lead" :object-id="leadId" />
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <el-card shadow="never" class="mb-4">
            <template #header>公司</template>
            <p class="text-sm">{{ ws.company.company_name }}</p>
            <p class="text-sm text-slate-600">{{ ws.company.company_type }}</p>
            <p v-if="ws.company.website" class="mt-2 text-sm">
              <a :href="String(ws.company.website)" target="_blank" rel="noreferrer" class="text-blue-600">网站</a>
            </p>
            <p v-if="ws.company.linkedin_url" class="text-sm">
              <a :href="String(ws.company.linkedin_url)" target="_blank" rel="noreferrer" class="text-blue-600">LinkedIn</a>
            </p>
            <el-button class="mt-3" size="small" @click="$router.push({ name: 'company-detail', params: { companyId: ws.company.id } })">打开公司</el-button>
          </el-card>
          <el-card shadow="never">
            <template #header>联系人</template>
            <template v-if="ws.contact">
              <p class="text-sm font-medium">{{ ws.contact.first_name }} {{ ws.contact.last_name }}</p>
              <p class="text-sm">{{ ws.contact.title || '—' }}</p>
              <p class="text-sm">{{ ws.contact.email || '—' }}</p>
              <p v-if="ws.contact.linkedin_url" class="text-sm">
                <a :href="String(ws.contact.linkedin_url)" target="_blank" rel="noreferrer" class="text-blue-600">联系人 LinkedIn</a>
              </p>
              <el-button
                v-if="ws.contact"
                class="mt-3"
                size="small"
                @click="$router.push({ name: 'contact-detail', params: { contactId: ws.contact.id } })"
              >打开联系人</el-button>
            </template>
            <p v-else class="text-sm text-slate-500">未指定主联系人</p>
          </el-card>
          <el-card shadow="never" class="mt-4">
            <template #header>最近互动 / 任务 / AI</template>
            <p class="text-xs text-slate-500">开放任务（{{ ws.open_tasks.length }}）</p>
            <ul class="max-h-40 overflow-auto text-sm">
              <li v-for="t in ws.open_tasks" :key="String(t.id)">{{ t.title }} — {{ t.status }}</li>
            </ul>
            <p class="mt-2 text-xs text-slate-500">最近 AI 产出</p>
            <ul class="max-h-40 overflow-auto text-sm">
              <li v-for="a in ws.recent_ai_outputs" :key="String(a.id)">{{ a.task_type }} — {{ a.status }}</li>
            </ul>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { http } from '@/api/http'
import { fetchLeadWorkspace, type LeadWorkspace } from '@/api/leadsWorkspace'
import { LEAD_PIPELINE_STAGES } from '@/constants/leadPipeline'
import {
  ObjectActivityLogPanel,
  ObjectAiActionsPanel,
  ObjectFilesPanel,
  ObjectInteractionsPanel,
  ObjectNotesPanel,
  ObjectTagsPanel,
  ObjectTasksPanel,
} from '@/components/object-panels'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const leadId = computed(() => route.params.leadId as string)

const loading = ref(false)
const ws = ref<LeadWorkspace | null>(null)
const tasksRef = ref<{ reload?: () => Promise<void> } | null>(null)
const activityRef = ref<{ reload?: () => Promise<void> } | null>(null)

const aiContext = computed(() => {
  const l = ws.value?.lead as Record<string, unknown> | undefined
  if (!l) return {}
  return { ...l }
})

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

function openIntelligenceWorkbench() {
  router.push({ name: 'lead-intelligence', query: { leadId: leadId.value } })
}

async function reloadWorkspace() {
  ws.value = await fetchLeadWorkspace(leadId.value)
  tasksRef.value?.reload?.()
  activityRef.value?.reload?.()
}

async function load() {
  loading.value = true
  try {
    ws.value = await fetchLeadWorkspace(leadId.value)
  } finally {
    loading.value = false
  }
}

async function setStage(st: string) {
  if (!ws.value || ws.value.lead.current_stage === st) return
  await ElMessageBox.confirm(`将阶段切换为「${st}」？`, '确认')
  await http.post(`/leads/${leadId.value}/stage`, { current_stage: st })
  ElMessage.success('已更新阶段')
  await load()
  activityRef.value?.reload?.()
}

async function quickRfq() {
  if (!ws.value) return
  await http.post('/rfqs', {
    lead_id: leadId.value,
    company_id: ws.value.lead.company_id,
    contact_id: ws.value.contact?.id ?? null,
    status: 'Draft',
  })
  ElMessage.success('已创建 RFQ 草稿')
  await load()
}

async function quickSample() {
  if (!ws.value) return
  await http.post('/samples', {
    lead_id: leadId.value,
    company_id: ws.value.lead.company_id,
    contact_id: ws.value.contact?.id ?? null,
    sample_status: 'Requested',
  })
  ElMessage.success('已创建样品申请')
  await load()
}

async function markDormant() {
  await http.post(`/leads/${leadId.value}/stage`, { current_stage: 'Dormant' })
  ElMessage.success('已标为 Dormant')
  await load()
}

async function markStrategic() {
  if (!ws.value) return
  await http.put(`/companies/${ws.value.lead.company_id}`, { strategic_level: 'strategic' })
  ElMessage.success('公司已标为战略级（strategic）')
  await load()
}

watch(leadId, () => load())
onMounted(load)
</script>
