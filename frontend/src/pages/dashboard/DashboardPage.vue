<template>
  <div class="space-y-6" v-loading="loading">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-800">行动看板</h2>
      <div class="flex gap-2">
        <el-button size="small" type="primary" plain @click="router.push({ name: 'daily-decision-queue' })">今日决策队列</el-button>
        <el-button size="small" type="success" plain @click="router.push({ name: 'commercial-intelligence' })">商业智能</el-button>
        <el-button size="small" type="primary" plain @click="router.push({ name: 'demo-walkthrough' })">Demo walkthrough</el-button>
        <el-button size="small" type="warning" plain @click="router.push({ name: 'external-execution' })">外部执行 / Staging</el-button>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
    </div>
    <p class="text-sm text-slate-600">
      今日应联系谁、处理哪些 RFQ、跟进哪些样品与订单——集中在一页。规则生成的建议可点击跳转。
    </p>

    <BusinessExecutionCommandCenter :data="businessExecution" />

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 class="text-base font-semibold text-slate-900">今日运营决策队列</h3>
          <p class="mt-1 max-w-4xl text-sm text-slate-600">
            按 P0/P1、owner、due date、partner/product focus、readiness impact 和风险排序，直接告诉团队今天先推进什么。
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <el-tag type="danger" effect="plain">P0 {{ decisionQueue?.summary.p0 ?? 0 }}</el-tag>
          <el-tag type="warning" effect="plain">P1 {{ decisionQueue?.summary.p1 ?? 0 }}</el-tag>
          <el-tag type="primary" effect="plain">Staging/D9 {{ decisionQueue?.summary.staging_or_d9 ?? 0 }}</el-tag>
          <el-tag type="success" effect="plain">Pilot {{ decisionQueue?.summary.pilot ?? 0 }}</el-tag>
          <el-tag type="info" effect="plain">外部输入 {{ decisionQueue?.summary.external_input_required ?? 0 }}</el-tag>
          <el-tag type="primary" effect="plain">我的 {{ decisionQueue?.summary.my_items ?? 0 }}</el-tag>
          <el-tag type="danger" effect="plain">处理阻塞 {{ decisionQueue?.summary.blocked ?? 0 }}</el-tag>
          <el-tag type="warning" effect="plain">等外部 {{ decisionQueue?.summary.waiting_external ?? 0 }}</el-tag>
          <el-tag type="info" effect="plain">逾期 follow-up {{ decisionQueue?.summary.overdue_followups ?? 0 }}</el-tag>
        </div>
      </div>
      <el-alert
        class="mb-3"
        type="warning"
        :closable="false"
        show-icon
        title="队列只做内部行动排序：不自动发送外部消息、不记录 raw token、不把本地检查当真实 staging evidence、不改报价或订单状态。"
      />
      <el-table :data="decisionQueue?.items || []" border size="small" empty-text="暂无今日运营决策项">
        <el-table-column label="优先动作" min-width="280">
          <template #default="{ row }">
            <div class="font-semibold text-slate-900">{{ row.title }}</div>
            <div class="mt-1 flex flex-wrap gap-1">
              <el-tag size="small" :type="priorityTag(row.priority)" effect="plain">{{ row.priority }}</el-tag>
              <el-tag size="small" effect="plain">{{ row.category }}</el-tag>
              <el-tag v-if="row.affects_d9" size="small" type="danger" effect="plain">影响 D9</el-tag>
              <el-tag v-if="row.affects_pilot" size="small" type="success" effect="plain">影响 Pilot</el-tag>
            </div>
            <p class="mt-1 text-xs text-slate-500">{{ row.reason }}</p>
          </template>
        </el-table-column>
        <el-table-column label="Owner / 风险" min-width="200">
          <template #default="{ row }">
            <div class="text-sm text-slate-700">{{ row.owner || '未指定' }}</div>
            <el-tag class="mt-1" size="small" effect="plain">{{ row.severity }}</el-tag>
            <div v-if="row.handling" class="mt-2 rounded bg-slate-50 p-2 text-xs text-slate-600">
              <div>处理：{{ handlingStatusLabel(row.handling.handling_status) }}</div>
              <div v-if="row.handling.owner">接手人：{{ row.handling.owner }}</div>
              <div v-if="row.handling.follow_up_date">跟进：{{ row.handling.follow_up_date }}</div>
            </div>
            <p class="mt-1 text-xs text-slate-500">{{ row.risk }}</p>
          </template>
        </el-table-column>
        <el-table-column label="Partner / Product" min-width="240">
          <template #default="{ row }">
            <div class="text-sm font-medium text-slate-800">{{ row.partner_focus || row.customer_or_account || '内部运营' }}</div>
            <div class="mt-1 flex flex-wrap gap-1">
              <el-tag v-for="item in row.product_focus.slice(0, 5)" :key="item" size="small" effect="plain">{{ item }}</el-tag>
              <el-tag v-if="row.product_focus.length > 5" size="small" type="info" effect="plain">+{{ row.product_focus.length - 5 }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="下一步 / 依赖" min-width="320">
          <template #default="{ row }">
            <p class="text-sm text-slate-700">{{ row.next_action }}</p>
            <div class="mt-2 flex flex-wrap gap-1">
              <el-tag v-if="row.needs_business_signoff" size="small" effect="plain">business sign-off</el-tag>
              <el-tag v-if="row.needs_security_signoff" size="small" effect="plain">security sign-off</el-tag>
              <el-tag v-if="row.needs_partner_feedback" size="small" effect="plain">partner feedback</el-tag>
              <el-tag v-if="row.needs_staging_credentials" size="small" effect="plain">staging credentials</el-tag>
              <el-tag v-if="row.depends_on_external_input" size="small" type="warning" effect="plain">真实外部输入</el-tag>
            </div>
            <p v-if="row.handling?.internal_note" class="mt-2 text-xs text-slate-500">处理备注：{{ row.handling.internal_note }}</p>
            <p v-if="row.handling?.blocked_reason" class="mt-2 text-xs text-rose-600">阻塞原因：{{ row.handling.blocked_reason }}</p>
            <p v-if="row.handling?.decision_summary" class="mt-2 text-xs text-emerald-700">内部决策：{{ row.handling.decision_summary }}</p>
          </template>
        </el-table-column>
        <el-table-column label="协作处理" width="260" fixed="right">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-button size="small" type="primary" plain @click="quickHandle(row, 'acknowledge')">知晓</el-button>
              <el-button size="small" type="success" plain @click="quickHandle(row, 'assign')">接手</el-button>
              <el-button size="small" type="warning" plain @click="quickHandle(row, 'wait_external')">等外部</el-button>
              <el-button size="small" plain @click="openHandlingDialog(row, 'defer')">延期/备注</el-button>
              <el-button size="small" type="danger" plain @click="openHandlingDialog(row, 'mark_blocked')">阻塞</el-button>
              <el-button size="small" type="primary" link @click="router.push(row.source_path)">进入源对象</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 class="text-base font-semibold text-slate-900">每日操作地图</h3>
          <p class="mt-1 max-w-4xl text-sm text-slate-600">
            从这里开始当天工作：业务开发看客户与 Campaign / 营销活动，运营交付看订单、物流与反馈，管理者看 Partner、产品方向和市场响应。
          </p>
        </div>
        <el-tag type="info" effect="plain">READY_FOR_STAGING_HANDOFF</el-tag>
      </div>

      <el-alert
        v-if="supportWarning"
        class="mb-4"
        type="warning"
        :closable="false"
        show-icon
        title="部分操作地图数据暂不可用"
        :description="supportWarning"
      />

      <div class="grid gap-3 lg:grid-cols-3">
        <div v-for="entry in operatingMap" :key="entry.title" class="rounded border border-slate-100 bg-slate-50 p-3">
          <div class="flex items-start justify-between gap-2">
            <div>
              <div class="text-xs font-medium text-slate-500">{{ entry.perspective }}</div>
              <h4 class="mt-1 font-semibold text-slate-900">{{ entry.title }}</h4>
            </div>
            <el-tag :type="entry.tone" effect="plain">{{ entry.metric }}</el-tag>
          </div>
          <p class="mt-2 min-h-10 text-sm text-slate-600">{{ entry.description }}</p>
          <p class="mt-2 text-xs text-slate-500">{{ entry.nextAction }}</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <el-button v-for="link in entry.links" :key="link.path" size="small" type="primary" plain @click="router.push(link.path)">
              {{ link.label }}
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <DailyOperationsPanel />

    <ProductOpportunitySummary />

    <EndOfDaySummaryPanel />

    <el-collapse class="border-0">
      <el-collapse-item title="更多行动看板（RFQ / 样品 / 订单 / 任务）" name="legacy">
        <div class="space-y-6 pt-2">
          <el-card shadow="never">
            <template #header>今日行动</template>
            <div class="grid gap-3 md:grid-cols-2">
              <div>
                <div class="mb-2 text-sm font-medium text-slate-700">今日到期任务</div>
                <ActionTaskList :items="data?.due_today_tasks" @go="goTask" />
              </div>
              <div>
                <div class="mb-2 text-sm font-medium text-slate-700">今日计划跟进（线索）</div>
                <ActionLeadList :items="data?.leads_follow_up_due_today" />
              </div>
            </div>
          </el-card>

          <el-card shadow="never">
            <template #header>逾期 / 风险</template>
            <div class="grid gap-4 md:grid-cols-3">
              <div>
                <div class="mb-2 text-sm font-medium text-rose-700">逾期任务</div>
                <ActionTaskList :items="data?.overdue_tasks" @go="goTask" />
              </div>
              <div>
                <div class="mb-2 text-sm font-medium text-rose-700">跟进已过期线索</div>
                <ActionLeadList :items="data?.leads_needing_follow_up" />
              </div>
              <div>
                <div class="mb-2 text-sm font-medium text-rose-700">订单节点延误</div>
                <ul v-if="data?.orders_delayed_milestones?.length" class="space-y-1 text-sm">
                  <li v-for="m in data.orders_delayed_milestones" :key="m.milestone_id">
                    <router-link class="text-blue-600 hover:underline" :to="{ name: 'order-detail', params: { orderId: m.order_id } }">
                      {{ m.order_number }} — {{ m.milestone_name }}
                    </router-link>
                  </li>
                </ul>
                <p v-else class="text-sm text-slate-500">暂无</p>
              </div>
            </div>
          </el-card>

          <el-row :gutter="16">
            <el-col :xs="24" :md="12">
              <el-card shadow="never">
                <template #header>本周任务 &amp; 热门线索</template>
                <p class="mb-2 text-xs text-slate-500">本周到期</p>
                <ActionTaskList :items="data?.this_week_tasks" @go="goTask" />
                <p class="mb-2 mt-4 text-xs text-slate-500">高优先级线索</p>
                <ActionLeadList :items="data?.hot_leads" />
              </el-card>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-card shadow="never">
                <template #header>线索动态</template>
                <p class="mb-2 text-xs text-slate-500">最近有互动</p>
                <ActionLeadList :items="data?.leads_recent_activity" />
                <p class="mb-2 mt-4 text-xs text-slate-500">等待下一步</p>
                <ActionLeadList :items="data?.leads_waiting_next_step" />
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="16">
            <el-col :xs="24" :md="8">
              <el-card shadow="never">
                <template #header>RFQ 关注</template>
                <p class="text-xs text-slate-500">等待伙伴报价</p>
                <RfqMini :items="data?.rfqs_waiting_partner_quote" />
                <p class="mt-3 text-xs text-slate-500">客户评审中</p>
                <RfqMini :items="data?.rfqs_customer_reviewing" />
                <p class="mt-3 text-xs text-slate-500">谈判中</p>
                <RfqMini :items="data?.rfqs_negotiating" />
              </el-card>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-card shadow="never">
                <template #header>样品关注</template>
                <p class="text-xs text-slate-500">已申请</p>
                <SampleMini :items="data?.samples_requested" />
                <p class="mt-3 text-xs text-slate-500">运输中</p>
                <SampleMini :items="data?.samples_shipped" />
                <p class="mt-3 text-xs text-slate-500">已签收待反馈</p>
                <SampleMini :items="data?.samples_delivered_no_feedback" />
                <p class="mt-3 text-xs text-slate-500">跟进到期</p>
                <SampleMini :items="data?.samples_follow_up_due" />
              </el-card>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-card shadow="never">
                <template #header>订单风险</template>
                <p class="text-xs text-slate-500">高风险订单</p>
                <ul v-if="data?.high_risk_orders?.length" class="space-y-1 text-sm">
                  <li v-for="o in data.high_risk_orders" :key="o.id">
                    <router-link :to="{ name: 'order-detail', params: { orderId: o.id } }" class="text-blue-600 hover:underline">
                      {{ o.order_number }}
                    </router-link>
                    <span class="text-slate-500">（{{ o.risk_level }}）</span>
                  </li>
                </ul>
                <p v-else class="text-sm text-slate-500">暂无</p>
                <p class="mt-3 text-xs text-slate-500">交期临近但缺少 ETA / 海运记录</p>
                <ul v-if="data?.orders_eta_missing?.length" class="space-y-1 text-sm">
                  <li v-for="o in data.orders_eta_missing" :key="'m-' + o.id">
                    <router-link :to="{ name: 'order-detail', params: { orderId: o.id } }" class="text-blue-600 hover:underline">
                      {{ o.order_number }}
                    </router-link>
                  </li>
                </ul>
                <p v-else class="text-sm text-slate-500">暂无</p>
                <p class="mt-3 text-xs text-slate-500">ETA 已过仍未交付</p>
                <ul v-if="data?.orders_eta_passed_not_delivered?.length" class="space-y-1 text-sm">
                  <li v-for="o in data.orders_eta_passed_not_delivered" :key="'e-' + o.id">
                    <router-link :to="{ name: 'order-detail', params: { orderId: o.id } }" class="text-blue-600 hover:underline">
                      {{ o.order_number }}
                    </router-link>
                  </li>
                </ul>
                <p v-else class="text-sm text-slate-500">暂无</p>
              </el-card>
            </el-col>
          </el-row>

          <el-card shadow="never">
            <template #header>推荐下一步（规则生成）</template>
            <ul v-if="data?.recommended_actions?.length" class="space-y-2">
              <li v-for="a in data.recommended_actions" :key="a.id" class="rounded border border-slate-100 bg-white p-3 text-sm">
                <div class="font-medium text-slate-800">{{ a.title }}</div>
                <div class="text-slate-600">{{ a.message }}</div>
                <el-button class="mt-2" size="small" type="primary" link @click="followRec(a)">前往处理</el-button>
              </li>
            </ul>
            <p v-else class="text-sm text-slate-500">暂无新建议</p>
          </el-card>

          <el-card shadow="never">
            <template #header>最近 AI 产出</template>
            <ul v-if="data?.recent_ai_outputs?.length" class="text-sm space-y-1">
              <li v-for="x in data.recent_ai_outputs" :key="x.id">
                <router-link to="/ai-outputs" class="text-blue-600 hover:underline">{{ x.task_type }}</router-link>
                <span class="text-slate-400"> · {{ x.status }}</span>
              </li>
            </ul>
            <p v-else class="text-sm text-slate-500">暂无</p>
          </el-card>
        </div>
      </el-collapse-item>
    </el-collapse>

    <el-dialog v-model="handlingDialogVisible" title="处理今日运营决策项" width="560px">
      <div v-if="handlingTarget" class="space-y-3">
        <div>
          <div class="text-sm font-semibold text-slate-900">{{ handlingTarget.title }}</div>
          <p class="mt-1 text-xs text-slate-500">
            只记录内部处理，不写真实签字、不写 staging evidence、不自动修改源对象。
          </p>
        </div>
        <el-form label-position="top">
          <el-form-item label="处理动作">
            <el-select v-model="handlingForm.action" class="w-full">
              <el-option label="知晓" value="acknowledge" />
              <el-option label="接手 / 分配 owner" value="assign" />
              <el-option label="延期" value="defer" />
              <el-option label="标记阻塞" value="mark_blocked" />
              <el-option label="等待外部输入" value="wait_external" />
              <el-option label="记录内部决策" value="record_decision" />
              <el-option label="追加内部备注" value="add_note" />
            </el-select>
          </el-form-item>
          <el-form-item label="Owner">
            <el-input v-model="handlingForm.owner" placeholder="例如 operator@example.com" />
          </el-form-item>
          <el-form-item label="Follow-up 日期">
            <el-date-picker v-model="handlingForm.follow_up_date" class="w-full" type="date" value-format="YYYY-MM-DD" placeholder="选择后续跟进日期" />
          </el-form-item>
          <el-form-item label="内部备注">
            <el-input v-model="handlingForm.internal_note" type="textarea" :rows="3" placeholder="记录内部处理进展；不要粘贴 token、真实签字或未确认外部回复。" />
          </el-form-item>
          <el-form-item label="阻塞原因">
            <el-input v-model="handlingForm.blocked_reason" type="textarea" :rows="2" placeholder="仅在 blocked 时填写，例如等待 business/security/staging 外部输入。" />
          </el-form-item>
          <el-form-item label="内部决策摘要">
            <el-input v-model="handlingForm.decision_summary" type="textarea" :rows="2" placeholder="仅记录内部判断，不声明 approved / complete / STAGING_VALIDATED。" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="handlingDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="handlingSaving" @click="saveHandling">保存处理记录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  fetchDailyDecisionQueue,
  fetchBusinessExecution,
  fetchDashboardActions,
  updateDailyQueueHandling,
  type BusinessExecution,
  type DailyDecisionQueue,
  type DailyDecisionQueueItem,
  type DashboardActions,
  type RecommendedAction,
} from '@/api/dashboard'
import { fetchFeedbackTickets, type FeedbackTicketList } from '@/api/feedbackTickets'
import { fetchGrowthOperationsConsole, type GrowthOperationsConsole } from '@/api/growthOperations'
import {
  fetchMarketResponseIntelligence,
  fetchMarketResponseReviews,
  type MarketResponseIntelligence,
  type MarketResponseReviewConsole,
} from '@/api/marketResponse'
import { fetchPartnerOnboarding, type PartnerOnboardingResponse } from '@/api/partnerOnboarding'
import { fetchExternalExecutionConsole, type ExternalExecutionConsole } from '@/api/externalExecution'
import ActionTaskList from './dashboard/ActionTaskList.vue'
import ActionLeadList from './dashboard/ActionLeadList.vue'
import RfqMini from './dashboard/RfqMini.vue'
import SampleMini from './dashboard/SampleMini.vue'
import DailyOperationsPanel from '@/components/dashboard/DailyOperationsPanel.vue'
import ProductOpportunitySummary from '@/components/dashboard/ProductOpportunitySummary.vue'
import EndOfDaySummaryPanel from '@/components/dashboard/EndOfDaySummaryPanel.vue'
import BusinessExecutionCommandCenter from '@/components/dashboard/BusinessExecutionCommandCenter.vue'

const router = useRouter()
const loading = ref(false)
const data = ref<DashboardActions | null>(null)
const businessExecution = ref<BusinessExecution | null>(null)
const decisionQueue = ref<DailyDecisionQueue | null>(null)
const growth = ref<GrowthOperationsConsole | null>(null)
const feedback = ref<FeedbackTicketList | null>(null)
const market = ref<MarketResponseIntelligence | null>(null)
const marketReviews = ref<MarketResponseReviewConsole | null>(null)
const partner = ref<PartnerOnboardingResponse | null>(null)
const externalExecution = ref<ExternalExecutionConsole | null>(null)
const supportWarning = ref('')
const handlingDialogVisible = ref(false)
const handlingSaving = ref(false)
const handlingTarget = ref<DailyDecisionQueueItem | null>(null)
const handlingForm = ref({
  action: 'add_note',
  owner: '',
  follow_up_date: '',
  blocked_reason: '',
  internal_note: '',
  decision_summary: '',
})

type OperatingMapEntry = {
  perspective: string
  title: string
  metric: string
  tone: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  description: string
  nextAction: string
  links: Array<{ label: string; path: string }>
}

function numberLabel(value: number | null, unit = '项') {
  return value === null ? '加载中' : `${value} ${unit}`
}

function sumLengths(...items: Array<unknown[] | undefined>) {
  return items.reduce((total, item) => total + (item?.length || 0), 0)
}

function priorityTag(priority: string) {
  if (priority === 'P0') return 'danger'
  if (priority === 'P1') return 'warning'
  return 'info'
}

function handlingStatusLabel(status: string) {
  const labels: Record<string, string> = {
    new: '未处理',
    acknowledged: '已知晓',
    in_progress: '处理中',
    deferred: '已延期',
    blocked: '处理阻塞',
    waiting_external: '等待外部输入',
    decision_recorded: '已记录内部决策',
  }
  return labels[status] || status
}

function currentOwner() {
  return localStorage.getItem('partneros_email') || 'operator'
}

function handlingPayload(row: DailyDecisionQueueItem, action: string) {
  return {
    queue_item_id: row.id,
    source_type: row.source_type,
    source_id: row.source_id,
    source_path: row.source_path,
    title: row.title,
    category: row.category,
    priority: row.priority,
    partner_focus: row.partner_focus,
    product_focus: row.product_focus,
    customer_or_account: row.customer_or_account,
    action,
  }
}

async function quickHandle(row: DailyDecisionQueueItem, action: string) {
  try {
    const payload = {
      ...handlingPayload(row, action),
      owner: action === 'assign' ? currentOwner() : (row.handling?.owner || null),
      internal_note:
        action === 'wait_external'
          ? '等待真实外部输入；未收到回复前不得标记 approved、complete 或 response received。'
          : undefined,
    }
    await updateDailyQueueHandling(payload)
    ElMessage.success('已保存内部处理记录')
    await load()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存处理记录失败')
  }
}

function openHandlingDialog(row: DailyDecisionQueueItem, action: string) {
  handlingTarget.value = row
  handlingForm.value = {
    action,
    owner: row.handling?.owner || row.owner || currentOwner(),
    follow_up_date: row.handling?.follow_up_date || '',
    blocked_reason: row.handling?.blocked_reason || '',
    internal_note: row.handling?.internal_note || '',
    decision_summary: row.handling?.decision_summary || '',
  }
  handlingDialogVisible.value = true
}

async function saveHandling() {
  if (!handlingTarget.value) return
  handlingSaving.value = true
  try {
    await updateDailyQueueHandling({
      ...handlingPayload(handlingTarget.value, handlingForm.value.action),
      owner: handlingForm.value.owner || null,
      follow_up_date: handlingForm.value.follow_up_date || null,
      blocked_reason: handlingForm.value.blocked_reason || null,
      internal_note: handlingForm.value.internal_note || null,
      decision_summary: handlingForm.value.decision_summary || null,
    })
    handlingDialogVisible.value = false
    ElMessage.success('已保存内部处理记录')
    await load()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存处理记录失败')
  } finally {
    handlingSaving.value = false
  }
}

const operatingMap = computed<OperatingMapEntry[]>(() => {
  const campaignCount = growth.value
    ? growth.value.campaigns.filter((row) => ['planned', 'active'].includes(row.status)).length
    : null
  const quoteCount = data.value
    ? sumLengths(data.value.rfqs_waiting_partner_quote, data.value.rfqs_customer_reviewing, data.value.rfqs_negotiating)
    : null
  const orderRiskCount = data.value
    ? sumLengths(
        data.value.high_risk_orders,
        data.value.orders_delayed_milestones,
        data.value.orders_eta_missing,
        data.value.orders_eta_passed_not_delivered,
      )
    : null
  const feedbackCount = feedback.value?.total ?? null
  const marketCount = marketReviews.value
    ? marketReviews.value.reviews.filter((row) => ['needs review', 'blocked', 'watching'].includes(row.status)).length
    : (market.value?.summary.recommendation_count ?? market.value?.recommendations.length ?? null)
  const partnerGapCount = partner.value ? partner.value.items.filter((row) => row.missing_items.length > 0).length : null
  const externalBlockedCount = externalExecution.value
    ? externalExecution.value.actions.filter((row) => ['blocked', 'draft', 'ready to send'].includes(row.status)).length
    : null
  const stagingPendingCount = externalExecution.value
    ? externalExecution.value.staging_readiness.filter((row) => !['ready', 'verified', 'complete'].includes(row.status)).length
    : null
  const leadCount = data.value ? sumLengths(data.value.leads_follow_up_due_today, data.value.hot_leads, data.value.leads_needing_follow_up) : null

  return [
    {
      perspective: '业务开发',
      title: '客户开发与 Campaign 下一步',
      metric: numberLabel((leadCount ?? 0) + (campaignCount ?? 0)),
      tone: 'primary',
      description: `待跟进客户 ${numberLabel(leadCount)}，进行中 Campaign / 营销活动 ${numberLabel(campaignCount)}。HOSUN / JOOBOO / Future Partner 平级进入增长流程。`,
      nextAction: '先看客户与 Campaign，再创建人工外联任务；系统不自动发送外部消息。',
      links: [
        { label: '客户开发', path: '/lead-intelligence' },
        { label: '营销触达', path: '/growth-operations' },
      ],
    },
    {
      perspective: '业务开发',
      title: '报价机会与 RFQ',
      metric: numberLabel(quoteCount),
      tone: 'success',
      description: `待处理报价 / RFQ ${numberLabel(quoteCount)}，用于把客户兴趣转成报价机会和订单入口。`,
      nextAction: '复核 RFQ、报价目录和新建报价单，必要时创建或更新报价。',
      links: [
        { label: '报价单', path: '/quotes' },
        { label: 'RFQ', path: '/rfqs' },
      ],
    },
    {
      perspective: '运营交付',
      title: '订单交付与物流风险',
      metric: numberLabel(orderRiskCount),
      tone: orderRiskCount ? 'warning' : 'info',
      description: `订单、生产里程碑、ETA 缺口和物流风险 ${numberLabel(orderRiskCount)}，用于交付协同和客户可见状态维护。`,
      nextAction: '先处理高风险订单，再进入订单详情查看生产、shipment 和客户可见摘要。',
      links: [
        { label: '订单', path: '/orders' },
        { label: '交付协同', path: '/partner-operations' },
      ],
    },
    {
      perspective: '运营交付',
      title: '客户 Feedback 处理',
      metric: numberLabel(feedbackCount),
      tone: feedbackCount ? 'danger' : 'info',
      description: `未处理或待复核 feedback ${numberLabel(feedbackCount)}，只记录内部处理，不自动回复客户、不承诺 SLA。`,
      nextAction: '进入客户反馈队列，关联订单、物流风险和 response summary。',
      links: [{ label: '客户反馈', path: '/feedback-tickets' }],
    },
    {
      perspective: '管理决策',
      title: 'Market Response 待审查',
      metric: numberLabel(marketCount),
      tone: 'success',
      description: `Market Response 审查项 ${numberLabel(marketCount)}，把订单、物流、反馈和 onboarding 缺口沉淀为 HOSUN / JOOBOO / future partner 产品判断。`,
      nextAction: '优先处理 needs validation、internal-only 和 pilot blocker；customer-safe candidate 仍需业务确认后才能对外展示。',
      links: [
        { label: '市场响应', path: '/market-response' },
        { label: '审查队列', path: '/market-response?status=needs%20review' },
      ],
    },
    {
      perspective: '管理决策',
      title: 'Partner Onboarding 缺口',
      metric: numberLabel(partnerGapCount, '个 Partner'),
      tone: partnerGapCount ? 'warning' : 'info',
      description: `仍有缺口的 Partner ${numberLabel(partnerGapCount, '个')}。HOSUN、JOOBOO 与未来优质外贸品牌按同一接入规则管理。`,
      nextAction: '复核产品、报价、Portal、演示和交付准备度，补齐下一步动作。',
      links: [
        { label: 'Partner 接入', path: '/partner-onboarding' },
        { label: '外部执行', path: '/external-execution' },
        { label: '演示流程', path: '/demo-walkthrough' },
      ],
    },
    {
      perspective: '内部 Beta / Staging',
      title: '外部执行与 Staging Gate',
      metric: numberLabel((externalBlockedCount ?? 0) + (stagingPendingCount ?? 0)),
      tone: externalBlockedCount || stagingPendingCount ? 'warning' : 'info',
      description: `外部动作待处理 ${numberLabel(externalBlockedCount)}，staging / D9 前置条件待补 ${numberLabel(stagingPendingCount)}。本地 dry-run 不能替代真实 staging evidence。`,
      nextAction: '跟进 partner rehearsal、business sign-off、security review、credentials request 和 rollback owner；不记录 raw token，不写 STAGING_VALIDATED。',
      links: [
        { label: '阻塞动作', path: '/external-execution?status=blocked' },
        { label: '外部执行', path: '/external-execution' },
        { label: 'Staging readiness', path: '/staging-readiness' },
      ],
    },
  ]
})

function goTask(id: string) {
  router.push({ path: '/tasks', query: { focus: id } })
}

function followRec(a: RecommendedAction) {
  const id = a.object_id
  const t = a.object_type
  if (t === 'lead') router.push({ name: 'lead-detail', params: { leadId: id } })
  else if (t === 'rfq') router.push({ name: 'rfq-detail', params: { rfqId: id } })
  else if (t === 'sample') router.push({ name: 'sample-detail', params: { sampleId: id } })
  else if (t === 'order') router.push({ name: 'order-detail', params: { orderId: id } })
  else if (t === 'task') router.push({ path: '/tasks', query: { focus: id } })
  else router.push(a.path)
}

async function load() {
  loading.value = true
  supportWarning.value = ''
  try {
    data.value = await fetchDashboardActions()
    const supportResults = await Promise.allSettled([
      fetchBusinessExecution(),
      fetchDailyDecisionQueue(),
      fetchGrowthOperationsConsole(),
      fetchFeedbackTickets({ operation_filter: 'needs_internal_review', limit: 1 }),
      fetchMarketResponseIntelligence(),
      fetchMarketResponseReviews(),
      fetchPartnerOnboarding(),
      fetchExternalExecutionConsole(),
    ])
    if (supportResults[0].status === 'fulfilled') businessExecution.value = supportResults[0].value
    if (supportResults[1].status === 'fulfilled') decisionQueue.value = supportResults[1].value
    if (supportResults[2].status === 'fulfilled') growth.value = supportResults[2].value
    if (supportResults[3].status === 'fulfilled') feedback.value = supportResults[3].value
    if (supportResults[4].status === 'fulfilled') market.value = supportResults[4].value
    if (supportResults[5].status === 'fulfilled') marketReviews.value = supportResults[5].value
    if (supportResults[6].status === 'fulfilled') partner.value = supportResults[6].value
    if (supportResults[7].status === 'fulfilled') externalExecution.value = supportResults[7].value
    const failed = supportResults.filter((result) => result.status === 'rejected').length
    if (failed) supportWarning.value = `${failed} 个只读聚合接口暂不可用，核心行动看板仍可继续使用。`
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
