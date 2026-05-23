<template>
  <div v-loading="loading" class="space-y-4">
    <el-button link type="primary" @click="$router.push({ name: 'companies' })">← 返回公司列表</el-button>

    <template v-if="ws && company">
      <el-card shadow="never">
        <div class="grid gap-2 text-sm text-slate-800 md:grid-cols-2">
          <div>
            <h2 class="text-xl font-semibold">{{ company.company_name }}</h2>
            <p class="text-slate-600">{{ company.company_type }} · {{ company.status || '—' }} · 优先级 {{ company.priority || '—' }}</p>
            <p class="mt-1">
              <span v-if="company.website">
                <a :href="String(company.website)" target="_blank" rel="noreferrer" class="text-blue-600">网站</a>
                ·
              </span>
              <span v-if="company.linkedin_url">
                <a :href="String(company.linkedin_url)" target="_blank" rel="noreferrer" class="text-blue-600">LinkedIn</a>
              </span>
            </p>
            <p>{{ company.city || '—' }} / {{ company.state || '—' }} / {{ company.country || '—' }}</p>
            <p>行业 {{ company.industry || '—' }} · 规模 {{ company.size || '—' }}</p>
            <p>客群 {{ company.customer_segment || '—' }} · 战略 {{ company.strategic_level || '—' }}</p>
            <p>来源 {{ company.source || '—' }}</p>
            <p class="mt-1">兴趣标签 {{ company.product_interest_tags || '—' }}</p>
          </div>
          <div>
            <p class="font-medium text-slate-700">AI 摘要</p>
            <p class="whitespace-pre-wrap text-slate-600">{{ company.ai_profile_summary || '—' }}</p>
            <p class="mt-2 font-medium text-slate-700">AI 策略建议</p>
            <p class="whitespace-pre-wrap text-slate-600">{{ company.ai_recommended_strategy || '—' }}</p>
          </div>
        </div>
      </el-card>

      <CompanyEnrichmentPanel
        :company-id="companyId"
        :website="(company?.website as string) || null"
        @reloaded="reload"
      />

      <el-card shadow="never">
        <template #header>快捷动作</template>
        <div class="flex flex-wrap gap-2">
          <el-button size="small" @click="contactDialog = true">添加联系人</el-button>
          <el-button size="small" type="primary" @click="leadDialog = true">创建线索</el-button>
          <el-button size="small" @click="scrollTo('task-panel')">创建任务</el-button>
          <el-button size="small" @click="scrollTo('interaction-panel')">记录互动</el-button>
          <el-button size="small" @click="scrollTo('ai-panel')">AI 生成</el-button>
          <el-button size="small" @click="$router.push({ name: 'field-visits' })">地推拜访</el-button>
          <el-button size="small" type="primary" @click="quickRfq">创建 RFQ</el-button>
        </div>
      </el-card>

      <el-row :gutter="16">
        <el-col :xs="24" :lg="16">
          <el-card shadow="never" class="mb-4">
            <template #header>联系人</template>
            <el-table v-if="contacts.length" :data="contacts" size="small" stripe @row-click="onContactRow">
              <el-table-column label="姓名">
                <template #default="{ row }">
                  <router-link
                    class="text-blue-600 hover:underline"
                    :to="{ name: 'contact-detail', params: { contactId: row.id } }"
                    @click.stop
                  >
                    {{ row.first_name }} {{ row.last_name }}
                  </router-link>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="职位" />
              <el-table-column prop="email" label="邮箱" />
              <el-table-column prop="phone" label="电话" />
              <el-table-column prop="decision_maker_level" label="决策层级" width="110" />
            </el-table>
            <p v-else class="text-sm text-slate-500">暂无联系人</p>
          </el-card>

          <el-card shadow="never" class="mb-4">
            <template #header>线索</template>
            <el-table v-if="leads.length" :data="leads" size="small" stripe>
              <el-table-column label="名称">
                <template #default="{ row }">
                  <router-link
                    class="text-blue-600 hover:underline"
                    :to="{ name: 'lead-detail', params: { leadId: row.id } }"
                  >
                    {{ row.lead_name }}
                  </router-link>
                </template>
              </el-table-column>
              <el-table-column prop="current_stage" label="阶段" width="120" />
              <el-table-column prop="priority" label="优先级" width="90" />
              <el-table-column prop="source" label="来源" width="100" />
              <el-table-column prop="next_action_due_date" label="下次动作日" width="120" />
            </el-table>
            <p v-else class="text-sm text-slate-500">暂无线索</p>
          </el-card>

          <el-card shadow="never" class="mb-4">
            <template #header>关联对象</template>
            <div class="space-y-3 text-sm">
              <div>
                <div class="mb-1 font-medium">RFQ</div>
                <el-table v-if="relatedRfqs.length" :data="relatedRfqs" size="small">
                  <el-table-column prop="rfq_number" label="#" />
                  <el-table-column prop="status" label="状态" />
                </el-table>
                <p v-else class="text-slate-500">暂无</p>
              </div>
              <div>
                <div class="mb-1 font-medium">样品</div>
                <el-table v-if="relatedSamples.length" :data="relatedSamples" size="small">
                  <el-table-column prop="sample_request_number" label="#" />
                  <el-table-column prop="sample_status" label="状态" />
                </el-table>
                <p v-else class="text-slate-500">暂无</p>
              </div>
              <div>
                <div class="mb-1 font-medium">订单</div>
                <el-table v-if="relatedOrders.length" :data="relatedOrders" size="small">
                  <el-table-column prop="order_number" label="#" />
                  <el-table-column prop="production_status" label="生产" />
                </el-table>
                <p v-else class="text-slate-500">暂无</p>
              </div>
              <div>
                <div class="mb-1 font-medium">地推</div>
                <el-table v-if="relatedFv.length" :data="relatedFv" size="small">
                  <el-table-column prop="plan_name" label="计划" />
                  <el-table-column prop="status" label="状态" />
                </el-table>
                <p v-else class="text-slate-500">暂无</p>
              </div>
            </div>
          </el-card>

          <div id="ai-panel">
            <ObjectAiActionsPanel
              object-type="company"
              :object-id="companyId"
              variant="company"
              :ai-context="aiContext"
            />
          </div>
          <div id="interaction-panel" class="mt-4">
            <ObjectInteractionsPanel object-type="company" :object-id="companyId" @task-spawned="reload" />
          </div>
          <div id="task-panel" class="mt-4">
            <ObjectTasksPanel ref="tasksRef" object-type="company" :object-id="companyId" />
          </div>
          <div class="mt-4 grid gap-4 lg:grid-cols-2">
            <ObjectNotesPanel object-type="company" :object-id="companyId" />
            <ObjectTagsPanel object-type="company" :object-id="companyId" />
            <ObjectFilesPanel object-type="company" :object-id="companyId" />
            <div class="lg:col-span-2">
              <ObjectActivityLogPanel ref="activityRef" object-type="company" :object-id="companyId" />
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <el-card shadow="never" class="mb-4">
            <template #header>兴趣摘要</template>
            <p class="text-xs text-slate-500">线索数 {{ activeLeadCount }}</p>
            <p class="mt-2 text-sm">{{ tagLine }}</p>
          </el-card>
          <el-card shadow="never">
            <template #header>开放任务 / 最近 AI</template>
            <ul class="text-sm">
              <li v-for="t in openTasks" :key="t.id">{{ t.title }}</li>
            </ul>
            <ul class="mt-2 text-sm text-slate-600">
              <li v-for="a in recentAi" :key="a.id">{{ a.task_type }}</li>
            </ul>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <el-dialog v-model="contactDialog" title="新建联系人" width="480px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="名"><el-input v-model="contactForm.first_name" /></el-form-item>
        <el-form-item label="姓"><el-input v-model="contactForm.last_name" /></el-form-item>
        <el-form-item label="职位"><el-input v-model="contactForm.title" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="contactForm.email" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="contactDialog = false">取消</el-button>
        <el-button type="primary" @click="saveContact">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="leadDialog" title="新建线索" width="480px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model="leadForm.lead_name" /></el-form-item>
        <el-form-item label="来源"><el-input v-model="leadForm.source" /></el-form-item>
        <el-form-item label="类型"><el-input v-model="leadForm.lead_type" /></el-form-item>
        <el-form-item label="阶段"><el-input v-model="leadForm.current_stage" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="leadDialog = false">取消</el-button>
        <el-button type="primary" @click="saveLead">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { http } from '@/api/http'
import { fetchCompanyWorkspace } from '@/api/objectWorkspaces'
import {
  ObjectActivityLogPanel,
  ObjectAiActionsPanel,
  ObjectFilesPanel,
  ObjectInteractionsPanel,
  ObjectNotesPanel,
  ObjectTagsPanel,
  ObjectTasksPanel,
} from '@/components/object-panels'
import CompanyEnrichmentPanel from '@/components/enrichment/CompanyEnrichmentPanel.vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const companyId = computed(() => route.params.companyId as string)

const loading = ref(false)
const ws = ref<Record<string, unknown> | null>(null)
const tasksRef = ref<{ reload?: () => Promise<void> } | null>(null)
const activityRef = ref<{ reload?: () => void } | null>(null)

const company = computed(() => (ws.value?.company as Record<string, unknown> | undefined) ?? null)
const contacts = computed(() => (ws.value?.contacts as Record<string, unknown>[]) ?? [])
const leads = computed(() => (ws.value?.leads as Record<string, unknown>[]) ?? [])
const relatedRfqs = computed(() => (ws.value?.related_rfqs as Record<string, unknown>[]) ?? [])
const relatedSamples = computed(() => (ws.value?.related_samples as Record<string, unknown>[]) ?? [])
const relatedOrders = computed(() => (ws.value?.related_orders as Record<string, unknown>[]) ?? [])
const relatedFv = computed(() => (ws.value?.related_field_visits as Record<string, unknown>[]) ?? [])
const openTasks = computed(() => (ws.value?.open_tasks as { id: string; title: string }[]) ?? [])
const recentAi = computed(() => (ws.value?.recent_ai_outputs as { id: string; task_type: string }[]) ?? [])
const interest = computed(() => ws.value?.product_interest_summary as Record<string, unknown> | undefined)
const tagLine = computed(() => {
  const raw = interest.value?.tags_from_company
  const arr = Array.isArray(raw) ? (raw as unknown[]).map(String) : []
  return arr.length ? arr.join(', ') : '—'
})
const activeLeadCount = computed(() => {
  const v = interest.value?.active_lead_count
  return typeof v === 'number' ? v : 0
})

const aiContext = computed(() => ({ ...(company.value ?? {}) }))

const contactDialog = ref(false)
const leadDialog = ref(false)
const contactForm = reactive({
  first_name: '',
  last_name: '',
  title: '',
  email: '',
})
const leadForm = reactive({
  lead_name: '',
  source: 'Website',
  lead_type: 'Channel Lead',
  current_stage: 'New',
})

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

function onContactRow() {
  /* row-click placeholder — navigation via link */
}

async function reload() {
  ws.value = await fetchCompanyWorkspace(companyId.value)
  tasksRef.value?.reload?.()
  activityRef.value?.reload?.()
}

async function load() {
  loading.value = true
  try {
    ws.value = await fetchCompanyWorkspace(companyId.value)
  } finally {
    loading.value = false
  }
}

async function saveContact() {
  await http.post('/contacts', {
    ...contactForm,
    company_id: companyId.value,
  })
  ElMessage.success('已添加联系人')
  contactDialog.value = false
  await reload()
}

async function saveLead() {
  await http.post('/leads', {
    ...leadForm,
    company_id: companyId.value,
    primary_contact_id: null,
  })
  ElMessage.success('已创建线索')
  leadDialog.value = false
  await reload()
}

async function quickRfq() {
  await http.post('/rfqs', {
    lead_id: null,
    company_id: companyId.value,
    contact_id: null,
    status: 'Draft',
  })
  ElMessage.success('已创建 RFQ 草稿')
  await reload()
}

watch(companyId, () => load())
onMounted(load)
</script>
