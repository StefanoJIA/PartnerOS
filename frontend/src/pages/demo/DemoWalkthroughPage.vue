<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchMarketResponseIntelligence, type MarketResponseIntelligence } from '@/api/marketResponse'
import { fetchPortalOperationsConsole, type PortalOperationsConsole } from '@/api/portalOperations'
import { formatApiError } from '@/api/errors'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const portal = ref<PortalOperationsConsole | null>(null)
const market = ref<MarketResponseIntelligence | null>(null)

const safety =
  '只读演示指南。系统保持 READY_FOR_STAGING_HANDOFF，不进入 D9，不验证 staging，不通知客户或供应商，不发送邮件/webhook，不调用承运商，也不暴露 token/cost/margin/private-note 字段。'

const focusLabels: Record<string, string> = {
  adjustable_desk_frames: 'Adjustable desk frames',
  desk_legs: 'Desk legs',
  lifting_columns: 'Lifting columns',
  education_furniture: 'Education furniture',
  project_furniture: 'Project furniture',
}

const journey = computed(() => [
  {
    key: 'development',
    label: '客户开发',
    value: '品牌 + 项目线索',
    detail: '先确认客户需求、目标品牌方向和项目背景，再进入 Campaign / 营销活动和产品线匹配。',
    route: '/leads',
  },
  {
    key: 'campaign',
    label: 'Campaign / 营销活动',
    value: '人工外联任务',
    detail: '用 Growth Operations 规划 HOSUN / JOOBOO 分群、生成中英文草稿、记录人工状态；系统不自动发送。',
    route: '/growth-operations',
  },
  {
    key: 'interest',
    label: '产品适配',
    value: `${market.value?.summary.feedback_ticket_count ?? 0} feedback / ${market.value?.summary.market_signal_count ?? 0} market notes`,
    detail: '客户反馈、报价行、订单需求和市场记录共同说明哪个产品线值得跟进。',
    route: '/market-intelligence',
  },
  {
    key: 'quote',
    label: '报价',
    value: `${market.value?.summary.quote_count ?? 0} quotes`,
    detail: '报价仍由人工准备并经过安全边界控制；PartnerOS 不自动发送报价。',
    route: '/quotes',
  },
  {
    key: 'order',
    label: '订单',
    value: `${portal.value?.recent_customer_visible_orders.total ?? 0} customer-visible orders`,
    detail: '已确认订单成为客户交付跟踪的运营事实源。',
    route: '/orders',
  },
  {
    key: 'partner',
    label: 'Partner 分单',
    value: `${portal.value?.multi_partner_flow_readiness.split_count ?? 0} splits across ${portal.value?.multi_partner_flow_readiness.partners_with_orders ?? 0} partners`,
    detail: 'HOSUN、JOOBOO 和未来 partner 都是平级制造伙伴，不是平台默认主品牌。',
    route: '/partner-operations',
  },
  {
    key: 'production',
    label: '生产',
    value: `${portal.value?.customer_snapshot_readiness.production_visible_count ?? 0} orders with production visibility`,
    detail: '生产里程碑由运营维护，仅通过白名单摘要对客户可见。',
    route: '/portal-integration',
  },
  {
    key: 'shipment',
    label: '物流',
    value: `${portal.value?.shipment_readiness.total_count ?? 0} shipment plans`,
    detail: '物流计划由人工维护；不调用承运商 API，不发 webhook，不自动改为 shipped/delivered。',
    route: '/portal-integration',
  },
  {
    key: 'portal',
    label: 'Portal',
    value: `${portal.value?.customer_snapshot_readiness.snapshot_count ?? 0} customer snapshots`,
    detail: '客户 Portal 只读取白名单内的产品、订单、生产、物流、资料和反馈状态。',
    route: '/portal-integration',
  },
  {
    key: 'feedback',
    label: '反馈',
    value: `${portal.value?.feedback_operations.open_count ?? 0} open tickets`,
    detail: '反馈只进入内部处理队列，不自动回复，也不承诺 SLA。',
    route: '/feedback-tickets',
  },
  {
    key: 'response',
    label: '市场响应',
    value: `${market.value?.summary.recommendation_count ?? 0} recommendations`,
    detail: '运营人员先审查信号，再调整产品方向、partner playbook 或客户开发动作。',
    route: '/market-intelligence',
  },
])

const storyLine = computed(() => [
  '用 PartnerOS 判断客户项目，从 Campaign / 营销活动进入人工外联，匹配合适的 partner 产品线，并在报价转订单后保持运营链路连续。',
  '客户 Portal 仍是过滤后的桥接层：客户能查看产品、订单、生产、物流、资料和反馈状态，但看不到内部运营数据。',
  'Market Response 把订单、延期、物流风险和反馈转化为需要人工审查的产品与 partner 优先级。',
])

const scenarioCards = computed(() => [
  {
    title: 'HOSUN lifting systems',
    partner: hosunPartner.value?.partner_name || 'HOSUN',
    focus: 'Desk frames, desk legs, lifting columns, and heavy-duty lifting projects',
    story:
      '运营从升降办公需求出发，准备报价，将已确认订单分配给 HOSUN，跟踪生产 readiness，维护物流计划，并把物流/反馈信号带回市场响应。',
    route: { name: 'market', query: { focus_category: 'lifting_columns' } },
  },
  {
    title: 'JOOBOO education furniture',
    partner: secondaryPartner.value?.partner_name || 'JOOBOO / future partner',
    focus: 'Education furniture and project furniture programs',
    story:
      '同一运营闭环也适用于教室和项目制家具：匹配产品要求、项目报价、partner 分工、展示客户安全交付状态，并把反馈转成 partner focus。',
    route: { name: 'market', query: { focus_category: 'education_furniture' } },
  },
])

const partnerRows = computed(() => portal.value?.multi_partner_flow_readiness.items || [])
const hosunPartner = computed(() => partnerRows.value.find((row) => row.partner_name.toUpperCase().includes('HOSUN')))
const secondaryPartner = computed(() =>
  partnerRows.value.find((row) => {
    const name = row.partner_name.toUpperCase()
    return name.includes('JOOBOO') || name.includes('HUIJU') || name.includes('EDUCATION')
  }) || partnerRows.value.find((row) => row.partner_id !== hosunPartner.value?.partner_id),
)

const focusRows = computed(() =>
  [...(portal.value?.market_signal_preview.items || [])].sort((a, b) => b.signal_score - a.signal_score),
)

const demoOrders = computed(() => portal.value?.recent_customer_visible_orders.items.slice(0, 4) || [])
const featuredOrder = computed(() =>
  demoOrders.value.find(
    (row) =>
      row.portal_tracking.has_production_updates ||
      row.portal_tracking.has_active_shipment ||
      row.portal_tracking.has_open_feedback ||
      row.portal_tracking.has_visible_resources,
  ) || demoOrders.value[0],
)

const marketExplanationRows = computed(() =>
  focusRows.value.map((row) => ({
    ...row,
    reason: [
      row.order_line_count ? `${row.order_line_count} order line(s)` : '',
      row.ordered_quantity ? `${row.ordered_quantity} ordered units` : '',
      row.feedback_count ? `${row.feedback_count} feedback signal(s)` : '',
      row.delayed_or_blocked_production_count ? `${row.delayed_or_blocked_production_count} production risk(s)` : '',
      row.shipment_issue_count ? `${row.shipment_issue_count} shipment issue(s)` : '',
    ]
      .filter(Boolean)
      .join('; ') || '运营待观察分类',
  })),
)

interface DemoControlLink {
  label: string
  path: string | null
  orderId: string | null | undefined
  detail: string
}

const demoControlLinks = computed(() => [
  { label: '仪表盘', path: '/', orderId: null, detail: '从运营上下文和每日流程开始。' },
  { label: 'Portal 运营', path: '/portal-integration', orderId: null, detail: '展示客户 Portal readiness 和安全字段契约。' },
  { label: '市场响应', path: '/market-intelligence', orderId: null, detail: '解释产品和 partner focus 信号。' },
  { label: '订单', path: '/orders', orderId: null, detail: '打开已确认客户订单列表。' },
  { label: '重点订单详情', path: null, orderId: featuredOrder.value?.id, detail: '展示客户可见的生产、物流、资料和反馈摘要。' },
  { label: '客户反馈', path: '/feedback-tickets', orderId: null, detail: '操作内部客户反馈队列。' },
  { label: '报价单', path: '/quotes', orderId: null, detail: '展示报价到订单的连续性。' },
  { label: '外部执行 / Staging', path: '/external-execution', orderId: null, detail: '把 rehearsal、UAT、security review 和 staging credentials 进入人工跟踪。' },
  { label: '系统健康', path: '/system-health', orderId: null, detail: '在现场演示前确认本地运行状态。' },
] satisfies DemoControlLink[])

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [portalData, marketData] = await Promise.all([
      fetchPortalOperationsConsole(),
      fetchMarketResponseIntelligence(),
    ])
    portal.value = portalData
    market.value = marketData
  } catch (e) {
    error.value = formatApiError(e, '演示场景加载失败。')
  } finally {
    loading.value = false
  }
}

function open(path: string) {
  router.push(path)
}

function openOrder(orderId: string | null | undefined) {
  if (orderId) router.push({ name: 'order-detail', params: { orderId } })
}

function openControlLink(link: DemoControlLink) {
  if (link.orderId) {
    openOrder(link.orderId)
    return
  }
  if (link.path) open(link.path)
}

function focusLabel(key: string) {
  return focusLabels[key] || key
}

onMounted(load)
</script>

<template>
  <div class="space-y-5" v-loading="loading">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">D8.4 业务演示流程</h2>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          面向 partner 的 PartnerOS 运营故事：客户开发、Campaign / 营销活动、人工外联、产品适配、报价、订单、partner 分单、生产、物流、Portal、反馈和市场响应。
        </p>
      </div>
      <div class="flex gap-2">
        <el-button @click="open('/')">仪表盘</el-button>
        <el-button type="primary" @click="load">刷新</el-button>
      </div>
    </div>

    <el-alert type="info" :closable="false" :title="safety" />
    <el-alert v-if="error" type="error" :closable="false" :title="error" />

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">演示故事线</h3>
        <el-tag effect="plain">代理操作系统</el-tag>
      </div>
      <div class="grid gap-3 lg:grid-cols-3">
        <div v-for="line in storyLine" :key="line" class="rounded border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
          {{ line }}
        </div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">运营闭环</h3>
        <el-tag type="success" effect="plain">READY_FOR_STAGING_HANDOFF</el-tag>
      </div>
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <button
          v-for="step in journey"
          :key="step.key"
          class="rounded border border-slate-200 bg-slate-50 p-3 text-left hover:border-blue-300 hover:bg-blue-50"
          @click="open(step.route)"
        >
          <div class="text-xs uppercase text-slate-500">{{ step.label }}</div>
          <div class="mt-1 text-lg font-semibold text-slate-900">{{ step.value }}</div>
          <p class="mt-2 text-sm text-slate-600">{{ step.detail }}</p>
        </button>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="font-semibold text-slate-800">演示快捷入口</h3>
          <p class="mt-1 text-sm text-slate-600">
            现场演示时用这些入口推进故事线，避免在导航中反复查找。
          </p>
        </div>
        <el-tag effect="plain">可重复演示路径</el-tag>
      </div>
      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <button
          v-for="link in demoControlLinks"
          :key="link.label"
          class="rounded border border-slate-200 bg-slate-50 p-3 text-left hover:border-blue-300 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="link.label === 'Featured Order Detail' && !link.orderId"
          @click="openControlLink(link)"
        >
          <div class="font-semibold text-slate-900">{{ link.label }}</div>
          <p class="mt-1 text-sm text-slate-600">{{ link.detail }}</p>
        </button>
      </div>
    </section>

    <div class="grid gap-5 xl:grid-cols-2">
      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h3 class="font-semibold text-slate-800">多 partner 覆盖</h3>
          <el-tag effect="plain">partner 平级</el-tag>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <div class="rounded border border-slate-100 p-3">
            <div class="text-xs uppercase text-slate-500">HOSUN 方向</div>
            <div class="mt-1 font-semibold text-slate-900">{{ hosunPartner?.partner_name || 'HOSUN lifting systems' }}</div>
            <p class="mt-2 text-sm text-slate-600">
              桌架、桌腿、升降柱和重载升降系统以运营信号呈现，不是硬编码的平台偏好。
            </p>
          </div>
          <div class="rounded border border-slate-100 p-3">
            <div class="text-xs uppercase text-slate-500">第二 partner 方向</div>
            <div class="mt-1 font-semibold text-slate-900">{{ secondaryPartner?.partner_name || 'JOOBOO education furniture' }}</div>
            <p class="mt-2 text-sm text-slate-600">
              教育家具和项目制家具证明 PartnerOS 可以支持多个外部品牌运营线。
            </p>
          </div>
        </div>
        <el-table :data="partnerRows" class="mt-4 w-full" size="small">
          <el-table-column prop="partner_name" label="Partner" min-width="190" />
          <el-table-column prop="order_count" label="订单" width="90" />
          <el-table-column prop="split_count" label="分单" width="90" />
          <el-table-column prop="active_shipment_count" label="物流" width="110" />
          <el-table-column label="风险" min-width="160">
            <template #default="{ row }">
              <span v-if="!row.risk_flags.length" class="text-slate-400">无风险</span>
              <el-tag v-for="flag in row.risk_flags" v-else :key="flag" size="small" type="warning" effect="plain">
                {{ flag }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h3 class="font-semibold text-slate-800">两条演示场景</h3>
          <el-tag type="success" effect="plain">HOSUN + JOOBOO</el-tag>
        </div>
        <div class="grid gap-3">
          <button
            v-for="scenario in scenarioCards"
            :key="scenario.title"
            class="rounded border border-slate-100 bg-slate-50 p-3 text-left hover:border-blue-300 hover:bg-blue-50"
            @click="router.push(scenario.route)"
          >
            <div class="text-xs uppercase text-slate-500">{{ scenario.partner }}</div>
            <div class="mt-1 font-semibold text-slate-900">{{ scenario.title }}</div>
            <p class="mt-1 text-sm font-medium text-slate-700">{{ scenario.focus }}</p>
            <p class="mt-2 text-sm text-slate-600">{{ scenario.story }}</p>
          </button>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h3 class="font-semibold text-slate-800">客户可见重点订单</h3>
          <el-button size="small" :disabled="!featuredOrder" @click="openOrder(featuredOrder?.id)">打开订单</el-button>
        </div>
        <template v-if="featuredOrder">
          <div class="rounded border border-slate-100 bg-slate-50 p-3">
            <div class="text-lg font-semibold text-slate-900">{{ featuredOrder.order_number }}</div>
            <div class="mt-1 text-sm text-slate-600">{{ featuredOrder.company_name || '客户账号' }}</div>
            <div class="mt-3 grid gap-2 md:grid-cols-2">
              <el-tag effect="plain">{{ featuredOrder.portal_tracking.label || featuredOrder.portal_tracking.stage || 'Portal stage' }}</el-tag>
              <el-tag :type="featuredOrder.portal_tracking.has_production_updates ? 'success' : 'info'" effect="plain">
                生产 {{ featuredOrder.portal_tracking.has_production_updates ? '可见' : '待更新' }}
              </el-tag>
              <el-tag :type="featuredOrder.portal_tracking.has_active_shipment ? 'success' : 'warning'" effect="plain">
                物流 {{ featuredOrder.portal_tracking.active_shipment_count }}
              </el-tag>
              <el-tag :type="featuredOrder.portal_tracking.has_open_feedback ? 'warning' : 'info'" effect="plain">
                反馈 {{ featuredOrder.portal_tracking.open_feedback_count }}
              </el-tag>
            </div>
            <p class="mt-3 text-sm text-slate-600">{{ featuredOrder.portal_tracking.next_action_label || 'Review next customer-visible update.' }}</p>
          </div>
        </template>
        <el-empty v-else description="暂无客户可见订单" />
      </section>
    </div>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">市场响应信号说明</h3>
        <el-button size="small" @click="open('/market-intelligence')">打开市场响应</el-button>
      </div>
      <el-table :data="marketExplanationRows" class="w-full">
        <el-table-column label="方向" min-width="190">
          <template #default="{ row }">{{ focusLabel(row.key) }}</template>
        </el-table-column>
        <el-table-column prop="signal_score" label="分数" width="90" />
        <el-table-column prop="primary_signal" label="主信号" width="160" />
        <el-table-column prop="review_label" label="审查" min-width="210" />
        <el-table-column prop="reason" label="关注原因" min-width="360" />
        <el-table-column label="动作" width="110">
          <template #default="{ row }">
            <el-button size="small" @click="router.push({ name: 'market', query: row.route_query })">审查</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">Portal 运营演示依据</h3>
        <el-button size="small" @click="open('/portal-integration')">打开 Portal 运营</el-button>
      </div>
      <div class="grid gap-3 md:grid-cols-4">
        <div class="rounded border border-slate-100 p-3">
          <div class="text-xs uppercase text-slate-500">近期订单</div>
          <div class="mt-1 text-2xl font-semibold">{{ portal?.recent_customer_visible_orders.total ?? 0 }}</div>
        </div>
        <div class="rounded border border-slate-100 p-3">
          <div class="text-xs uppercase text-slate-500">物流风险</div>
          <div class="mt-1 text-2xl font-semibold">
            {{ (portal?.shipment_readiness.missing_estimated_dates_count ?? 0) + (portal?.shipment_readiness.shipped_without_tracking_count ?? 0) }}
          </div>
        </div>
        <div class="rounded border border-slate-100 p-3">
          <div class="text-xs uppercase text-slate-500">未结反馈</div>
          <div class="mt-1 text-2xl font-semibold">{{ portal?.feedback_operations.open_count ?? 0 }}</div>
        </div>
        <div class="rounded border border-slate-100 p-3">
          <div class="text-xs uppercase text-slate-500">市场信号</div>
          <div class="mt-1 text-2xl font-semibold">{{ portal?.market_signal_preview.total ?? 0 }}</div>
        </div>
      </div>
    </section>
  </div>
</template>
