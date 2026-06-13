<template>
  <div class="space-y-6" v-loading="loading">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-800">行动看板</h2>
      <div class="flex gap-2">
        <el-button size="small" type="primary" plain @click="router.push({ name: 'demo-walkthrough' })">Demo walkthrough</el-button>
        <el-button size="small" type="warning" plain @click="router.push({ name: 'external-execution' })">外部执行 / Staging</el-button>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
    </div>
    <p class="text-sm text-slate-600">
      今日应联系谁、处理哪些 RFQ、跟进哪些样品与订单——集中在一页。规则生成的建议可点击跳转。
    </p>

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
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchDashboardActions, type DashboardActions, type RecommendedAction } from '@/api/dashboard'
import { fetchFeedbackTickets, type FeedbackTicketList } from '@/api/feedbackTickets'
import { fetchGrowthOperationsConsole, type GrowthOperationsConsole } from '@/api/growthOperations'
import { fetchMarketResponseIntelligence, type MarketResponseIntelligence } from '@/api/marketResponse'
import { fetchPartnerOnboarding, type PartnerOnboardingResponse } from '@/api/partnerOnboarding'
import ActionTaskList from './dashboard/ActionTaskList.vue'
import ActionLeadList from './dashboard/ActionLeadList.vue'
import RfqMini from './dashboard/RfqMini.vue'
import SampleMini from './dashboard/SampleMini.vue'
import DailyOperationsPanel from '@/components/dashboard/DailyOperationsPanel.vue'
import ProductOpportunitySummary from '@/components/dashboard/ProductOpportunitySummary.vue'
import EndOfDaySummaryPanel from '@/components/dashboard/EndOfDaySummaryPanel.vue'

const router = useRouter()
const loading = ref(false)
const data = ref<DashboardActions | null>(null)
const growth = ref<GrowthOperationsConsole | null>(null)
const feedback = ref<FeedbackTicketList | null>(null)
const market = ref<MarketResponseIntelligence | null>(null)
const partner = ref<PartnerOnboardingResponse | null>(null)
const supportWarning = ref('')

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
  const marketCount = market.value?.summary.recommendation_count ?? market.value?.recommendations.length ?? null
  const partnerGapCount = partner.value ? partner.value.items.filter((row) => row.missing_items.length > 0).length : null
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
      nextAction: '复核 RFQ、报价目录和价格预览，必要时创建或更新报价。',
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
      title: 'Market Response 推荐',
      metric: numberLabel(marketCount),
      tone: 'success',
      description: `市场响应建议 ${numberLabel(marketCount)}，结合订单需求、生产/物流风险、客户反馈和 watchlist 判断产品方向。`,
      nextAction: '用市场信号判断是否继续推进某个 partner / product focus。',
      links: [{ label: '市场响应', path: '/market-response' }],
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
      fetchGrowthOperationsConsole(),
      fetchFeedbackTickets({ operation_filter: 'needs_internal_review', limit: 1 }),
      fetchMarketResponseIntelligence(),
      fetchPartnerOnboarding(),
    ])
    if (supportResults[0].status === 'fulfilled') growth.value = supportResults[0].value
    if (supportResults[1].status === 'fulfilled') feedback.value = supportResults[1].value
    if (supportResults[2].status === 'fulfilled') market.value = supportResults[2].value
    if (supportResults[3].status === 'fulfilled') partner.value = supportResults[3].value
    const failed = supportResults.filter((result) => result.status === 'rejected').length
    if (failed) supportWarning.value = `${failed} 个只读聚合接口暂不可用，核心行动看板仍可继续使用。`
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
