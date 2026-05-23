<template>
  <div v-loading="loading" class="space-y-4">
    <el-card shadow="never">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 class="text-lg font-semibold text-slate-800">A 域 · Lead Intelligence 工作台</h2>
            <p class="mt-1 text-xs text-slate-500">
              公司 → 联系人 → 情报标签 / 市场信号 → 可解释评分 → 互动记录 → 下一步动作（D5 最小闭环）
            </p>
          </div>
          <el-select
            v-model="selectedLeadId"
            filterable
            clearable
            placeholder="选择线索"
            class="min-w-[240px]"
            :loading="leadsLoading"
            @visible-change="onLeadsDropdown"
          >
            <el-option v-for="l in leadOptions" :key="l.id" :label="l.lead_name" :value="l.id" />
          </el-select>
        </div>
      </template>
      <p v-if="!selectedLeadId" class="text-sm text-slate-500">请选择一条线索以加载情报工作流。</p>
    </el-card>

    <template v-if="wf && selectedLeadId">
      <el-row :gutter="16">
        <el-col :xs="24" :lg="14">
          <el-card shadow="never" class="mb-4">
            <template #header>公司与联系人</template>
            <div class="space-y-2 text-sm">
              <div>
                <span class="font-medium text-slate-700">{{ wf.company.company_name }}</span>
                <router-link
                  class="ml-2 text-xs text-blue-600"
                  :to="{ name: 'company-detail', params: { companyId: wf.company.id } }"
                >
                  公司详情
                </router-link>
              </div>
              <div v-if="wf.company.strategic_level" class="text-slate-600">
                战略层级：{{ wf.company.strategic_level }}
              </div>
              <div class="text-slate-600">
                <span class="font-medium">意向标签：</span>
                {{ wf.company.product_interest_tags || '—' }}
              </div>
              <div class="text-slate-600">
                <span class="font-medium">业务描述：</span>
                {{ wf.company.business_description || '—' }}
              </div>
              <el-divider class="my-2" />
              <div v-if="wf.primary_contact">
                <span class="font-medium">主联系人：</span>
                {{ wf.primary_contact.first_name }} {{ wf.primary_contact.last_name }}
                <span v-if="wf.primary_contact.title"> · {{ wf.primary_contact.title }}</span>
                <router-link
                  class="ml-2 text-xs text-blue-600"
                  :to="{ name: 'contact-detail', params: { contactId: wf.primary_contact.id } }"
                >
                  联系人
                </router-link>
              </div>
              <el-alert v-else type="warning" :closable="false" show-icon title="未设置主联系人" class="mt-2" />
            </div>
          </el-card>

          <el-card shadow="never" class="mb-4">
            <template #header>线索与市场情报</template>
            <div class="space-y-2 text-sm text-slate-700">
              <div>
                <span class="font-medium">{{ wf.lead.lead_name }}</span>
                <router-link class="ml-2 text-xs text-blue-600" :to="{ name: 'lead-detail', params: { leadId: wf.lead.id } }">
                  线索详情
                </router-link>
              </div>
              <div>阶段：{{ wf.lead.current_stage }} · 优先级：{{ wf.lead.priority || '—' }}</div>
              <div>商机意向：{{ wf.lead.product_interest || '—' }}</div>
              <div>
                已关联市场情报条目：
                <strong>{{ wf.market_intelligence_count }}</strong>
                <router-link
                  class="ml-2 text-xs text-blue-600"
                  :to="{ path: '/market-intelligence', query: { companyId: wf.company.id } }"
                >
                  按公司筛选查看
                </router-link>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="10">
          <el-card shadow="never" class="mb-4">
            <template #header>情报评分（可解释）</template>
            <div v-if="wf.market_fit_segments?.length" class="mb-3 flex flex-wrap gap-1">
              <el-tag
                v-for="seg in wf.market_fit_segments"
                :key="seg"
                size="small"
                :type="segmentTagType(seg)"
                effect="plain"
                :title="segmentTooltip(seg)"
              >
                {{ segmentLabel(seg) }}
              </el-tag>
            </div>
            <p v-else class="mb-3 text-xs text-slate-500">No segment assigned yet.</p>
            <div class="mb-3 text-center">
              <span class="text-4xl font-bold text-slate-800">{{ wf.intelligence_score }}</span>
              <span class="text-slate-500">/100</span>
            </div>
            <el-table :data="scoreRows" size="small" stripe>
              <el-table-column prop="k" label="维度" />
              <el-table-column prop="v" label="得分" width="72" />
            </el-table>
            <ul v-if="wf.suggested_next_actions?.length" class="mt-3 list-disc space-y-1 pl-5 text-xs text-slate-600">
              <li v-for="(s, i) in wf.suggested_next_actions" :key="i">{{ s }}</li>
            </ul>
            <p v-else class="mt-3 text-xs text-slate-500">No suggestions available yet.</p>
          </el-card>

          <el-card shadow="never">
            <template #header>记录触达并更新 Next Action</template>
            <p class="mb-3 text-sm text-slate-600">
              <span class="font-medium">当前 Next Action：</span>
              {{ wf.lead.next_action?.trim() ? wf.lead.next_action : 'No next action set.' }}
            </p>
            <el-form label-position="top" class="text-sm">
              <el-form-item label="互动类型">
                <el-input v-model="touch.interaction_type" placeholder="如 follow_up_call" />
              </el-form-item>
              <el-form-item label="渠道">
                <el-input v-model="touch.channel" placeholder="如 phone / email / visit" />
              </el-form-item>
              <el-form-item label="主题">
                <el-input v-model="touch.subject" />
              </el-form-item>
              <el-form-item label="摘要">
                <el-input v-model="touch.summary" type="textarea" :rows="2" />
              </el-form-item>
              <el-form-item label="线索下一步（写入 Lead.next_action）">
                <el-input v-model="touch.next_action" />
              </el-form-item>
              <el-form-item label="下次跟进日">
                <el-date-picker v-model="touchDue" type="date" value-format="YYYY-MM-DD" class="w-full" />
              </el-form-item>
              <el-form-item label="本条互动的待办（写入 Interaction）">
                <el-input v-model="touch.interaction_next_action" />
              </el-form-item>
              <el-button type="primary" :loading="saving" @click="submitTouchpoint">保存互动与下一步</el-button>
            </el-form>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { LeadIntelligenceWorkflow, TouchpointBody } from '@/api/aDomain'
import { fetchLeadIntelligenceWorkflow, postLeadIntelligenceTouchpoint } from '@/api/aDomain'
import { http } from '@/api/http'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const leadsLoading = ref(false)
const saving = ref(false)
const wf = ref<LeadIntelligenceWorkflow | null>(null)
const leadOptions = ref<{ id: string; lead_name: string }[]>([])
const selectedLeadId = ref<string | null>((route.query.leadId as string) || null)

const touch = ref<TouchpointBody>({
  interaction_type: 'follow_up',
  channel: 'call',
  subject: '',
  summary: '',
  next_action: '',
  interaction_next_action: '',
})
const touchDue = ref<string | null>(null)

const scoreRows = computed(() => {
  if (!wf.value) return []
  return Object.entries(wf.value.score_breakdown).map(([k, v]) => ({ k, v }))
})

const SEGMENT_LABELS: Record<string, string> = {
  lift_system_signal: 'Lifting System Signal',
  general_office_furniture_only: 'General Office Furniture',
  oem_odm_fit: 'OEM/ODM Project',
  medical_vertical: 'Medical / Healthcare Vertical',
  education_vertical: 'Education Vertical',
  heavy_duty_fit: 'Heavy-Duty / Industrial',
  project_based_furniture: 'Project-Based Furniture',
}

const SEGMENT_TOOLTIPS: Record<string, string> = {
  lift_system_signal: '已出现明确升降/可调桌架类意向信号，适合优先与升降系统业务对齐跟进。',
  general_office_furniture_only:
    '属于办公家具相关行业，但当前未见明确升降桌、桌架、桌腿、升降柱等意向。可低频维护或待信息补充后再评估（非负面）。',
  oem_odm_fit: 'OEM/ODM 或项目制升降方案信号，建议核对工程与认证路径。',
  medical_vertical: '医疗/医护/实验室场景相关。',
  education_vertical: '教育场景相关。',
  heavy_duty_fit: '重载或工业级升降需求信号。',
  project_based_furniture: '项目制家具、合同内装或安装交付相关。',
}

function segmentLabel(slug: string) {
  return SEGMENT_LABELS[slug] || slug
}

function segmentTooltip(slug: string) {
  return SEGMENT_TOOLTIPS[slug] || ''
}

function segmentTagType(slug: string): 'primary' | 'success' | 'info' | 'warning' | 'danger' {
  if (slug === 'general_office_furniture_only') return 'info'
  if (slug === 'lift_system_signal') return 'success'
  return 'primary'
}

watch(
  () => route.query.leadId,
  (q) => {
    if (typeof q === 'string' && q) selectedLeadId.value = q
  },
)

watch(selectedLeadId, (id) => {
  if (id) {
    router.replace({ query: { ...route.query, leadId: id } })
    loadWorkflow(id)
  } else {
    wf.value = null
    router.replace({ query: { ...route.query, leadId: undefined } })
  }
})

async function loadLeadsOnce() {
  if (leadOptions.value.length) return
  leadsLoading.value = true
  try {
    const { data } = await http.get<{ items: { id: string; lead_name: string }[] }>('/leads?limit=100')
    leadOptions.value = data.items
  } finally {
    leadsLoading.value = false
  }
}

function onLeadsDropdown(open: boolean) {
  if (open) void loadLeadsOnce()
}

async function loadWorkflow(leadId: string) {
  loading.value = true
  try {
    wf.value = await fetchLeadIntelligenceWorkflow(leadId)
    touch.value = {
      interaction_type: 'follow_up',
      channel: 'call',
      subject: `跟进 · ${wf.value.lead.lead_name}`,
      summary: '',
      next_action: wf.value.lead.next_action || '',
      interaction_next_action: '',
    }
    touchDue.value = wf.value.lead.next_action_due_date || null
  } catch (e: unknown) {
    wf.value = null
    ElMessage.error('加载工作流失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function submitTouchpoint() {
  if (!selectedLeadId.value) return
  saving.value = true
  try {
    await postLeadIntelligenceTouchpoint(selectedLeadId.value, {
      ...touch.value,
      next_action_due_date: touchDue.value || undefined,
    })
    ElMessage.success('已记录互动并更新下一步')
    await loadWorkflow(selectedLeadId.value)
  } catch (e: unknown) {
    ElMessage.error('保存失败')
    console.error(e)
  } finally {
    saving.value = false
  }
}

if (selectedLeadId.value) void loadWorkflow(selectedLeadId.value)
</script>
