<template>
  <div v-loading="loading" class="space-y-4">
    <el-button link type="primary" @click="$router.push({ name: 'contacts' })">← 返回联系人</el-button>

    <template v-if="ws && contact">
      <el-row :gutter="16">
        <el-col :xs="24" :lg="16">
          <el-card shadow="never">
            <h2 class="text-xl font-semibold">{{ contact.first_name }} {{ contact.last_name }}</h2>
            <p class="text-sm text-slate-600">{{ contact.title || '—' }} · {{ contact.contact_type || '—' }}</p>
            <p class="mt-2 text-sm">邮箱 {{ contact.email || '—' }} · 电话 {{ contact.phone || '—' }}</p>
            <p v-if="contact.linkedin_url" class="text-sm">
              <a :href="String(contact.linkedin_url)" target="_blank" rel="noreferrer" class="text-blue-600">LinkedIn</a>
            </p>
            <p class="text-sm">地区 {{ contact.location || '—' }}</p>
            <p class="text-sm">决策层级 {{ contact.decision_maker_level || '—' }} · 沟通偏好 {{ contact.communication_preference || '—' }}</p>
            <p class="text-sm">上次联系 {{ contact.last_contacted_at || '—' }} · 下次跟进 {{ contact.next_follow_up_at || '—' }}</p>
            <p class="text-sm">状态 {{ contact.status || '—' }}</p>
            <p class="mt-2 whitespace-pre-wrap text-sm text-slate-700">{{ contact.notes || '' }}</p>
          </el-card>

          <el-card shadow="never" class="mt-4">
            <template #header>快捷动作</template>
            <div class="flex flex-wrap gap-2">
              <el-button size="small" @click="scrollTo('ai-panel')">AI 文案</el-button>
              <el-button size="small" @click="scrollTo('interaction-panel')">记录互动</el-button>
              <el-button size="small" @click="scrollTo('task-panel')">创建任务</el-button>
              <el-button size="small" type="primary" @click="quickLead">创建线索</el-button>
              <el-button size="small" type="primary" @click="quickRfq">创建 RFQ</el-button>
              <el-button size="small" @click="$router.push({ name: 'field-visits' })">地推</el-button>
            </div>
          </el-card>

          <el-card shadow="never" class="mt-4">
            <template #header>关联线索</template>
            <el-table v-if="relatedLeads.length" :data="relatedLeads" size="small">
              <el-table-column label="名称">
                <template #default="{ row }">
                  <router-link class="text-blue-600" :to="{ name: 'lead-detail', params: { leadId: row.id } }">{{
                    row.lead_name
                  }}</router-link>
                </template>
              </el-table-column>
              <el-table-column prop="current_stage" width="120" />
              <el-table-column prop="next_action_due_date" width="120" />
            </el-table>
            <p v-else class="text-sm text-slate-500">暂无</p>
          </el-card>

          <el-card shadow="never" class="mt-4">
            <template #header>RFQ / 样品 / 订单</template>
            <p class="text-xs text-slate-500">RFQ {{ relatedRfqs.length }} · 样品 {{ relatedSamples.length }} · 订单 {{ relatedOrders.length }}</p>
          </el-card>

          <div id="ai-panel" class="mt-4">
            <ObjectAiActionsPanel object-type="contact" :object-id="contactId" variant="contact" :ai-context="aiContext" />
          </div>
          <div id="interaction-panel" class="mt-4">
            <ObjectInteractionsPanel object-type="contact" :object-id="contactId" @task-spawned="reload" />
          </div>
          <div id="task-panel" class="mt-4">
            <ObjectTasksPanel ref="tasksRef" object-type="contact" :object-id="contactId" />
          </div>
          <div class="mt-4 grid gap-4 lg:grid-cols-2">
            <ObjectNotesPanel object-type="contact" :object-id="contactId" />
            <ObjectTagsPanel object-type="contact" :object-id="contactId" />
            <ObjectFilesPanel object-type="contact" :object-id="contactId" />
            <div class="lg:col-span-2">
              <ObjectActivityLogPanel ref="activityRef" object-type="contact" :object-id="contactId" />
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :lg="8">
          <el-card v-if="companyCard" shadow="never">
            <template #header>公司</template>
            <p class="font-medium">{{ companyCard.company_name }}</p>
            <p class="text-sm text-slate-600">{{ companyCard.company_type }}</p>
            <el-button class="mt-3" size="small" type="primary" @click="openCompany">打开公司</el-button>
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
import { fetchContactWorkspace } from '@/api/objectWorkspaces'
import {
  ObjectActivityLogPanel,
  ObjectAiActionsPanel,
  ObjectFilesPanel,
  ObjectInteractionsPanel,
  ObjectNotesPanel,
  ObjectTagsPanel,
  ObjectTasksPanel,
} from '@/components/object-panels'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const contactId = computed(() => route.params.contactId as string)

const loading = ref(false)
const ws = ref<Record<string, unknown> | null>(null)
const tasksRef = ref<{ reload?: () => Promise<void> } | null>(null)
const activityRef = ref<{ reload?: () => void } | null>(null)

const contact = computed(() => (ws.value?.contact as Record<string, unknown> | undefined) ?? null)
const companyCard = computed(() => (ws.value?.company as Record<string, unknown> | undefined) ?? null)
const relatedLeads = computed(() => (ws.value?.related_leads as Record<string, unknown>[]) ?? [])
const relatedRfqs = computed(() => (ws.value?.related_rfqs as unknown[]) ?? [])
const relatedSamples = computed(() => (ws.value?.related_samples as unknown[]) ?? [])
const relatedOrders = computed(() => (ws.value?.related_orders as unknown[]) ?? [])

const aiContext = computed(() => ({ ...(contact.value ?? {}) }))

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

function openCompany() {
  const id = companyCard.value?.id as string | undefined
  if (id) router.push({ name: 'company-detail', params: { companyId: id } })
}

async function reload() {
  ws.value = await fetchContactWorkspace(contactId.value)
  tasksRef.value?.reload?.()
  activityRef.value?.reload?.()
}

async function load() {
  loading.value = true
  try {
    ws.value = await fetchContactWorkspace(contactId.value)
  } finally {
    loading.value = false
  }
}

async function quickLead() {
  const c = contact.value
  if (!c?.company_id) return
  await http.post('/leads', {
    lead_name: `Lead: ${c.first_name} ${c.last_name}`,
    company_id: c.company_id,
    primary_contact_id: contactId.value,
    source: 'Contact workspace',
    lead_type: 'Channel Lead',
    current_stage: 'New',
  })
  ElMessage.success('已创建线索')
  await reload()
}

async function quickRfq() {
  const c = contact.value
  if (!c?.company_id) return
  await http.post('/rfqs', {
    lead_id: null,
    company_id: c.company_id,
    contact_id: contactId.value,
    status: 'Draft',
  })
  ElMessage.success('已创建 RFQ')
  await reload()
}

watch(contactId, () => load())
onMounted(load)
</script>
