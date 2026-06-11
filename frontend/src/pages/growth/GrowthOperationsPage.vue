<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-semibold text-slate-900">增长运营闭环</h1>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          {{ data?.positioning_zh || '连接客户开发、Campaign / 营销活动、外联、报价、订单、Portal、反馈和市场响应。' }}
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <el-tag type="info" effect="plain">{{ data?.status || 'READY_FOR_STAGING_HANDOFF' }}</el-tag>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="安全边界：本页只做增长运营规划和人工动作记录，不连接销售易或 Constant Contact，不自动发送邮件/短信/LinkedIn，不修改报价或订单状态。"
    />
    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <el-skeleton v-if="loading && !data" animated :rows="8" />

    <template v-else-if="data">
      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 class="font-semibold text-slate-900">Campaign 工作台 / 营销活动</h2>
            <p class="mt-1 text-sm text-slate-600">
              保存 Campaign / 营销活动、人工外联任务和状态推进。操作顺序：规划活动 → 选择分群 → 创建外联任务 → 更新状态 →
              查看报价/订单/反馈/市场响应。系统只保存草稿与人工状态，不自动发送、不改报价或订单。
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <el-button size="small" @click="applyCampaignTemplate('hosun')">套用 HOSUN 示例</el-button>
            <el-button size="small" @click="applyCampaignTemplate('jooboo')">套用 JOOBOO 示例</el-button>
          </div>
        </div>

        <div class="grid gap-4 xl:grid-cols-[minmax(320px,420px)_1fr]">
          <div class="space-y-3 rounded border border-slate-100 bg-slate-50 p-3">
            <el-input v-model="campaignForm.name" placeholder="Campaign / 营销活动名称" />
            <div class="grid gap-2 sm:grid-cols-2">
              <el-input v-model="campaignForm.partner_focus" placeholder="Partner 方向，例如 HOSUN / JOOBOO" />
              <el-select v-model="campaignForm.status" placeholder="状态">
                <el-option label="已规划" value="planned" />
                <el-option label="推进中" value="active" />
                <el-option label="已暂停" value="paused" />
                <el-option label="已完成" value="completed" />
                <el-option label="已归档" value="archived" />
              </el-select>
            </div>
            <el-input v-model="campaignForm.product_focus_text" placeholder="产品方向，英文逗号分隔" />
            <el-input v-model="campaignForm.target_segment" placeholder="目标分群" />
            <el-input v-model="campaignForm.goal" type="textarea" :rows="2" placeholder="业务目标" />
            <el-input v-model="campaignForm.next_action" type="textarea" :rows="2" placeholder="下一步人工动作" />
            <div class="grid gap-2 sm:grid-cols-2">
              <el-input v-model="campaignForm.owner" placeholder="负责人" />
              <el-input v-model="campaignForm.notes" placeholder="备注" />
            </div>
            <el-button type="primary" :loading="savingCampaign" @click="saveCampaign">保存 Campaign / 营销活动</el-button>
          </div>

          <div class="min-w-0 space-y-3">
            <div class="flex flex-wrap items-center gap-2">
              <el-select v-model="selectedWorkspaceCampaignId" class="min-w-72" placeholder="选择已保存 Campaign / 营销活动">
                <el-option
                  v-for="row in workspaceCampaigns"
                  :key="row.id"
                  :label="`${row.name} · ${row.status_label}`"
                  :value="row.id"
                />
              </el-select>
              <el-button :disabled="!selectedWorkspaceCampaign" @click="advanceCampaignStatus('active')">标记推进中</el-button>
              <el-button :disabled="!selectedWorkspaceCampaign" @click="advanceCampaignStatus('paused')">暂停</el-button>
              <el-button :disabled="!selectedWorkspaceCampaign" @click="advanceCampaignStatus('completed')">完成</el-button>
            </div>

            <el-empty v-if="!selectedWorkspaceCampaign" description="暂无已保存 Campaign / 营销活动，请先创建 HOSUN 或 JOOBOO 示例。" />
            <template v-else>
              <div class="rounded border border-slate-100 p-3">
                <div class="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div class="font-medium text-slate-900">{{ selectedWorkspaceCampaign.name }}</div>
                    <div class="mt-1 text-xs text-slate-500">
                      {{ selectedWorkspaceCampaign.partner_focus }} · {{ selectedWorkspaceCampaign.status_label }} ·
                      {{ selectedWorkspaceCampaign.owner || '未指定负责人' }}
                    </div>
                  </div>
                  <el-tag type="success" effect="plain">HOSUN / JOOBOO 平级运营</el-tag>
                </div>
                <div class="mt-3 grid gap-2 text-sm text-slate-700 md:grid-cols-5">
                  <div>报价 {{ workspaceDetail?.summary.quote_count ?? selectedWorkspaceCampaign.summary?.quote_count ?? 0 }}</div>
                  <div>订单 {{ workspaceDetail?.summary.order_count ?? selectedWorkspaceCampaign.summary?.order_count ?? 0 }}</div>
                  <div>反馈 {{ workspaceDetail?.summary.feedback_ticket_count ?? selectedWorkspaceCampaign.summary?.feedback_ticket_count ?? 0 }}</div>
                  <div>物流风险 {{ workspaceDetail?.summary.shipment_risk_count ?? selectedWorkspaceCampaign.summary?.shipment_risk_count ?? 0 }}</div>
                  <div>市场信号 {{ workspaceDetail?.summary.market_signal_count ?? selectedWorkspaceCampaign.summary?.market_signal_count ?? 0 }}</div>
                </div>
                <p class="mt-2 text-xs text-slate-500">
                  {{ workspaceDetail?.summary.explanation_zh || selectedWorkspaceCampaign.summary?.explanation_zh }}
                </p>
              </div>

              <div class="grid gap-3 lg:grid-cols-[320px_1fr]">
                <div class="space-y-2 rounded border border-slate-100 bg-slate-50 p-3">
                  <h3 class="text-sm font-medium text-slate-900">创建人工外联任务</h3>
                  <el-select v-model="taskForm.task_type" placeholder="任务类型">
                    <el-option label="人工外联" value="manual_outreach" />
                    <el-option label="需求确认" value="qualification" />
                    <el-option label="报价跟进" value="quote_follow_up" />
                    <el-option label="反馈复盘" value="feedback_follow_up" />
                  </el-select>
                  <el-select v-model="taskForm.language" placeholder="草稿语言">
                    <el-option label="中文" value="zh" />
                    <el-option label="英文" value="en" />
                  </el-select>
                  <el-input v-model="taskForm.due_date" placeholder="到期日期，例如 2026-06-15" />
                  <el-input v-model="taskForm.draft_subject" placeholder="草稿标题，可留空自动生成" />
                  <el-input v-model="taskForm.draft_body" type="textarea" :rows="4" placeholder="草稿正文，可留空自动生成" />
                  <el-input v-model="taskForm.notes" placeholder="任务备注" />
                  <el-button type="primary" :loading="savingTask" @click="saveTask">创建任务草稿</el-button>
                </div>

                <el-table :data="workspaceDetail?.tasks || []" border empty-text="暂无人工任务">
                  <el-table-column label="任务" min-width="210">
                    <template #default="{ row }">
                      <div class="font-medium text-slate-900">{{ row.task_type_label }}</div>
                      <div class="text-xs text-slate-500">{{ row.language }} · {{ row.due_date || '未设到期日' }}</div>
                    </template>
                  </el-table-column>
                  <el-table-column label="草稿" min-width="280">
                    <template #default="{ row }">
                      <div class="font-medium text-slate-800">{{ row.draft_subject || '未填写标题' }}</div>
                      <div class="line-clamp-2 text-xs text-slate-500">{{ row.draft_body || '未填写正文' }}</div>
                    </template>
                  </el-table-column>
                  <el-table-column label="人工状态" width="180">
                    <template #default="{ row }">
                      <el-select :model-value="row.status" size="small" @change="updateTaskStatusFromSelect(row.id, $event)">
                        <el-option
                          v-for="item in workspaceDetail?.manual_status_options || []"
                          :key="item.value"
                          :label="item.label"
                          :value="item.value"
                        />
                      </el-select>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>
          </div>
        </div>
      </section>

      <section class="grid gap-3 lg:grid-cols-3">
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="font-semibold text-slate-900">销售易能力适配</h2>
          <div class="mt-3 flex flex-wrap gap-2">
            <el-tag v-for="item in data.competitor_alignment.sales_yi_adapted" :key="item" effect="plain">
              {{ item }}
            </el-tag>
          </div>
        </div>
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="font-semibold text-slate-900">Constant Contact 能力适配</h2>
          <div class="mt-3 flex flex-wrap gap-2">
            <el-tag v-for="item in data.competitor_alignment.constant_contact_adapted" :key="item" effect="plain">
              {{ item }}
            </el-tag>
          </div>
        </div>
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="font-semibold text-slate-900">PartnerOS 差异</h2>
          <p class="mt-3 text-sm text-slate-600">{{ data.competitor_alignment.partneros_difference }}</p>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="font-semibold text-slate-900">Campaign / 营销活动规划视图</h2>
            <p class="mt-1 text-sm text-slate-600">
              每个 Campaign / 营销活动都绑定 Partner 方向、产品方向、目标分群、业务目标、状态和下一步人工动作。
            </p>
          </div>
          <el-tag type="success" effect="plain">HOSUN / JOOBOO / Future Partner 平级</el-tag>
        </div>
        <el-table :data="data.campaigns" border empty-text="暂无增长 Campaign / 营销活动">
          <el-table-column label="Campaign / 营销活动" min-width="230">
            <template #default="{ row }">
              <div class="font-medium text-slate-900">{{ row.name }}</div>
              <div class="text-xs text-slate-500">{{ row.partner_focus }} · {{ row.status }}</div>
            </template>
          </el-table-column>
          <el-table-column label="产品方向" min-width="260">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tag v-for="item in row.product_focus" :key="item" size="small" effect="plain">{{ item }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="target_segment" label="目标分群" min-width="190" />
          <el-table-column prop="goal" label="目标" min-width="280" />
          <el-table-column prop="next_action" label="下一步" min-width="320" />
          <el-table-column label="运营数据" width="210">
            <template #default="{ row }">
              <div class="text-xs text-slate-600">
                线索 {{ row.metrics.lead_count }} / 报价 {{ row.metrics.quote_count }} / 订单 {{ row.metrics.order_count }}
              </div>
              <div class="mt-1 text-xs text-slate-600">
                反馈 {{ row.metrics.feedback_ticket_count }} / 物流风险 {{ row.metrics.shipment_risk_count }} / 市场信号 {{ row.metrics.market_signal_count }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="入口" width="160" fixed="right">
            <template #default="{ row }">
              <div class="flex flex-col gap-1">
                <el-button size="small" link type="primary" @click="go(row.links.lead_intelligence)">线索</el-button>
                <el-button size="small" link type="primary" @click="go(row.links.market_response)">市场响应</el-button>
                <el-button size="small" link type="primary" @click="go(row.links.quotes)">报价</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="mb-3 font-semibold text-slate-900">轻量客户分群</h2>
          <el-table :data="data.segments" stripe max-height="420" empty-text="暂无分群">
            <el-table-column prop="segment_label" label="分群" min-width="190" />
            <el-table-column prop="company_count" label="公司" width="80" />
            <el-table-column prop="lead_count" label="线索" width="80" />
            <el-table-column prop="contact_count" label="联系人" width="90" />
            <el-table-column prop="recommended_use" label="用途" min-width="260" />
          </el-table>
        </div>

        <div class="rounded border border-slate-200 bg-white p-4">
          <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 class="font-semibold text-slate-900">手动外联序列</h2>
            <el-select v-model="selectedCampaignId" size="small" class="w-64">
              <el-option v-for="row in data.campaigns" :key="row.id" :label="row.name" :value="row.id" />
            </el-select>
          </div>

          <template v-if="selectedSequence">
            <div class="mb-3 rounded border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
              <div>目标公司：{{ selectedSequence.company_name }}</div>
              <div>线索：{{ selectedSequence.lead_name || '暂无匹配线索，先做 segment 复核' }}</div>
              <div>任务：{{ selectedSequence.follow_up_task.title }} · {{ selectedSequence.follow_up_task.due_date }}</div>
            </div>

            <div class="grid gap-3 lg:grid-cols-2">
              <div>
                <p class="mb-1 text-xs font-medium text-slate-600">中文草稿</p>
                <el-input readonly :model-value="selectedSequence.drafts.zh.subject" class="mb-2" />
                <el-input type="textarea" :rows="7" readonly :model-value="selectedSequence.drafts.zh.body" />
              </div>
              <div>
                <p class="mb-1 text-xs font-medium text-slate-600">英文草稿</p>
                <el-input readonly :model-value="selectedSequence.drafts.en.subject" class="mb-2" />
                <el-input type="textarea" :rows="7" readonly :model-value="selectedSequence.drafts.en.body" />
              </div>
            </div>

            <div class="mt-3 flex flex-wrap items-center gap-2">
              <el-select v-model="manualEvent" size="small" class="w-44">
                <el-option
                  v-for="item in selectedSequence.manual_event_options"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
              <el-button
                type="primary"
                size="small"
                :loading="recording"
                :disabled="!selectedSequence.lead_id"
                @click="recordManualEvent"
              >
                记录人工动作
              </el-button>
              <span class="text-xs text-slate-500">只写入 Lead touchpoint，不发送消息。</span>
            </div>
          </template>
        </div>
      </section>

      <section class="grid gap-5 xl:grid-cols-2">
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="mb-3 font-semibold text-slate-900">Campaign / 营销活动到报价和订单的归因</h2>
          <el-table :data="data.attribution" stripe>
            <el-table-column label="Campaign / 营销活动" min-width="220">
              <template #default="{ row }">{{ campaignName(row.campaign_id) }}</template>
            </el-table-column>
            <el-table-column prop="quote_count" label="报价" width="80" />
            <el-table-column prop="order_count" label="订单" width="80" />
            <el-table-column prop="quote_value" label="报价金额" width="120" />
            <el-table-column prop="order_value" label="订单金额" width="120" />
            <el-table-column prop="explanation_zh" label="说明" min-width="260" />
          </el-table>
        </div>

        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="mb-3 font-semibold text-slate-900">反馈 / 物流风险 / 市场信号回流</h2>
          <el-table :data="data.feedback_loop" stripe>
            <el-table-column label="Campaign / 营销活动" min-width="220">
              <template #default="{ row }">{{ campaignName(row.campaign_id) }}</template>
            </el-table-column>
            <el-table-column prop="feedback_ticket_count" label="反馈" width="80" />
            <el-table-column prop="shipment_risk_count" label="物流风险" width="100" />
            <el-table-column prop="market_signal_count" label="市场信号" width="100" />
            <el-table-column prop="recommendation_zh" label="回流动作" min-width="260" />
          </el-table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { postLeadIntelligenceTouchpoint } from '@/api/aDomain'
import { formatApiError } from '@/api/errors'
import {
  createGrowthCampaign,
  createGrowthCampaignTask,
  fetchGrowthCampaignDetail,
  fetchGrowthCampaigns,
  fetchGrowthOperationsConsole,
  updateGrowthCampaign,
  updateGrowthCampaignTask,
  type GrowthOperationsConsole,
  type GrowthCampaignWorkspaceDetail,
  type GrowthCampaignWorkspaceRow,
  type GrowthOutreachSequence,
} from '@/api/growthOperations'

const router = useRouter()
const data = ref<GrowthOperationsConsole | null>(null)
const workspaceCampaigns = ref<GrowthCampaignWorkspaceRow[]>([])
const workspaceDetail = ref<GrowthCampaignWorkspaceDetail | null>(null)
const loading = ref(false)
const error = ref('')
const selectedCampaignId = ref('')
const selectedWorkspaceCampaignId = ref('')
const manualEvent = ref('manual_sent')
const recording = ref(false)
const savingCampaign = ref(false)
const savingTask = ref(false)

const campaignForm = ref({
  name: '',
  partner_focus: 'HOSUN',
  product_focus_text: 'lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply',
  target_segment: '升降办公与项目制采购客户',
  goal: '把产品兴趣推进到人工外联、报价请求和订单交付复盘。',
  status: 'planned',
  owner: '运营团队',
  next_action: '人工筛选客户并创建外联任务。',
  notes: '',
})

const taskForm = ref({
  task_type: 'manual_outreach',
  language: 'zh',
  due_date: '',
  draft_subject: '',
  draft_body: '',
  notes: '',
})

const selectedSequence = computed<GrowthOutreachSequence | null>(() => {
  if (!data.value) return null
  return data.value.outreach_sequences.find((row) => row.campaign_id === selectedCampaignId.value) || null
})

const selectedWorkspaceCampaign = computed<GrowthCampaignWorkspaceRow | null>(() => {
  if (!selectedWorkspaceCampaignId.value) return workspaceCampaigns.value[0] || null
  return workspaceCampaigns.value.find((row) => row.id === selectedWorkspaceCampaignId.value) || null
})

watch(selectedSequence, (row) => {
  manualEvent.value = row?.manual_event_options[0]?.value || 'manual_sent'
})

watch(selectedWorkspaceCampaignId, (id) => {
  if (id) void loadWorkspaceDetail(id)
})

function campaignName(id: string): string {
  return data.value?.campaigns.find((row) => row.id === id)?.name || id
}

function go(path: string) {
  router.push(path)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [consoleData, workspaceData] = await Promise.all([fetchGrowthOperationsConsole(), fetchGrowthCampaigns()])
    data.value = consoleData
    workspaceCampaigns.value = workspaceData.campaigns
    if (!selectedCampaignId.value) selectedCampaignId.value = data.value.campaigns[0]?.id || ''
    if (!selectedWorkspaceCampaignId.value) {
      selectedWorkspaceCampaignId.value = workspaceCampaigns.value[0]?.id || ''
    }
    if (selectedWorkspaceCampaignId.value) {
      workspaceDetail.value = await fetchGrowthCampaignDetail(selectedWorkspaceCampaignId.value)
    } else {
      workspaceDetail.value = null
    }
  } catch (err) {
    error.value = formatApiError(err, '增长运营数据加载失败。')
  } finally {
    loading.value = false
  }
}

async function loadWorkspaceDetail(id?: string) {
  const targetId = id || selectedWorkspaceCampaignId.value
  if (!targetId) {
    workspaceDetail.value = null
    return
  }
  try {
    workspaceDetail.value = await fetchGrowthCampaignDetail(targetId)
    selectedWorkspaceCampaignId.value = targetId
  } catch (err) {
    ElMessage.error(formatApiError(err, 'Campaign / 营销活动详情加载失败。'))
  }
}

function applyCampaignTemplate(kind: 'hosun' | 'jooboo') {
  if (kind === 'jooboo') {
    campaignForm.value = {
      name: 'JOOBOO 教育家具项目制增长战役',
      partner_focus: 'JOOBOO',
      product_focus_text: 'education furniture, project furniture, classroom furniture, collaborative table',
      target_segment: '教育空间、学校项目、项目制家具采购客户',
      goal: '把教育家具和项目制家具兴趣推进到需求确认、项目报价和交付复盘。',
      status: 'planned',
      owner: '运营团队',
      next_action: '整理教育家具项目客户清单并创建人工外联任务。',
      notes: '用于证明 PartnerOS 支持多优质外贸品牌平级运营。',
    }
    return
  }
  campaignForm.value = {
    name: 'HOSUN 升降系统增长战役',
    partner_focus: 'HOSUN',
    product_focus_text: 'lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply',
    target_segment: '升降办公、人体工学、项目制采购客户',
    goal: '把升降桌架、桌腿、升降柱和重载升降系统兴趣推进到报价请求和订单交付。',
    status: 'planned',
    owner: '运营团队',
    next_action: '筛选目标客户并创建人工外联任务。',
    notes: 'HOSUN 是示例 partner 之一，不是唯一主品牌。',
  }
}

async function saveCampaign() {
  savingCampaign.value = true
  try {
    const detail = await createGrowthCampaign({
      name: campaignForm.value.name,
      partner_focus: campaignForm.value.partner_focus,
      product_focus: campaignForm.value.product_focus_text
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
      target_segment: campaignForm.value.target_segment,
      goal: campaignForm.value.goal,
      status: campaignForm.value.status,
      owner: campaignForm.value.owner,
      next_action: campaignForm.value.next_action,
      notes: campaignForm.value.notes,
    })
    selectedWorkspaceCampaignId.value = detail.campaign.id
    workspaceDetail.value = detail
    const list = await fetchGrowthCampaigns()
    workspaceCampaigns.value = list.campaigns
    ElMessage.success('已保存增长 Campaign / 营销活动。')
  } catch (err) {
    ElMessage.error(formatApiError(err, 'Campaign / 营销活动保存失败。'))
  } finally {
    savingCampaign.value = false
  }
}

async function advanceCampaignStatus(status: string) {
  const id = selectedWorkspaceCampaign.value?.id
  if (!id) return
  try {
    workspaceDetail.value = await updateGrowthCampaign(id, { status })
    const list = await fetchGrowthCampaigns()
    workspaceCampaigns.value = list.campaigns
    ElMessage.success('Campaign / 营销活动状态已更新。')
  } catch (err) {
    ElMessage.error(formatApiError(err, 'Campaign / 营销活动状态更新失败。'))
  }
}

async function saveTask() {
  const id = selectedWorkspaceCampaign.value?.id
  if (!id) {
    ElMessage.warning('请先选择或创建 Campaign / 营销活动。')
    return
  }
  savingTask.value = true
  try {
    workspaceDetail.value = await createGrowthCampaignTask(id, {
      task_type: taskForm.value.task_type,
      language: taskForm.value.language,
      due_date: taskForm.value.due_date || null,
      draft_subject: taskForm.value.draft_subject || null,
      draft_body: taskForm.value.draft_body || null,
      notes: taskForm.value.notes || null,
      status: 'planned',
    })
    taskForm.value.draft_subject = ''
    taskForm.value.draft_body = ''
    taskForm.value.notes = ''
    ElMessage.success('已创建人工外联任务草稿。')
  } catch (err) {
    ElMessage.error(formatApiError(err, '任务创建失败。'))
  } finally {
    savingTask.value = false
  }
}

async function updateTaskStatus(taskId: string, status: string) {
  try {
    workspaceDetail.value = await updateGrowthCampaignTask(taskId, { status })
    ElMessage.success('任务状态已更新。')
  } catch (err) {
    ElMessage.error(formatApiError(err, '任务状态更新失败。'))
  }
}

function updateTaskStatusFromSelect(taskId: string, value: unknown) {
  void updateTaskStatus(taskId, String(value))
}

async function recordManualEvent() {
  const sequence = selectedSequence.value
  if (!sequence?.lead_id) {
    ElMessage.warning('当前 Campaign / 营销活动暂无可记录的线索，请先在客户开发中补充线索。')
    return
  }
  recording.value = true
  try {
    const eventLabel = sequence.manual_event_options.find((item) => item.value === manualEvent.value)?.label || manualEvent.value
    await postLeadIntelligenceTouchpoint(sequence.lead_id, {
      interaction_type: 'growth_campaign_touchpoint',
      channel: sequence.channel,
      subject: `${campaignName(sequence.campaign_id)} · ${eventLabel}`,
      summary: `D8.13 增长运营记录：${eventLabel}。Campaign=${sequence.campaign_id}。仅记录人工动作，系统未自动发送。`,
      direction: 'outbound',
      next_action: sequence.follow_up_task.next_action,
      interaction_next_action: sequence.follow_up_task.next_action,
    })
    ElMessage.success('已记录人工增长触达动作。')
  } catch (err) {
    ElMessage.error(formatApiError(err, '人工动作记录失败。'))
  } finally {
    recording.value = false
  }
}

onMounted(load)
</script>
