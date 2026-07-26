<template>
  <section class="rounded border border-slate-200 bg-white p-4">
    <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="text-base font-semibold text-slate-900">经营执行主链</h3>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          把客户、机会、报价、产品、Partner、交付和反馈串成一条当天可推进的业务链路。样例、D8 演示账户和本地 dry-run 数据默认不进入主视图。
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <el-tag type="primary" effect="plain">真实客户 {{ realCounts.accounts }}</el-tag>
        <el-tag type="success" effect="plain">机会 {{ realCounts.opportunities }}</el-tag>
        <el-tag type="warning" effect="plain">报价 {{ realCounts.quotes }}</el-tag>
        <el-tag type="danger" effect="plain">交付风险 {{ realCounts.delivery }}</el-tag>
        <el-tag type="info" effect="plain">Partner {{ realCounts.partners }}</el-tag>
      </div>
    </div>

    <el-alert
      class="mb-4"
      type="warning"
      :closable="false"
      show-icon
      title="内部经营判断层：不自动发送外部消息，不改变报价或订单状态，不记录 raw token，不把本地信息写成真实 staging evidence。"
    />

    <div v-if="!data" class="rounded border border-slate-100 bg-slate-50 p-4 text-sm text-slate-500">
      正在加载经营执行主链。
    </div>

    <template v-else>
      <div
        v-if="hiddenSyntheticCount > 0"
        class="mb-4 rounded border border-amber-100 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        已从主视图隐藏 {{ hiddenSyntheticCount }} 条演示或虚拟构建数据。后续录入真实客户、报价、订单和反馈后，会进入这里的经营链路。
      </div>

      <div class="grid gap-3 lg:grid-cols-4">
        <section
          v-for="section in chainSections"
          :key="section.key"
          class="flex min-h-64 flex-col rounded border border-slate-100 bg-slate-50 p-3"
        >
          <div class="mb-3">
            <div class="flex items-center justify-between gap-2">
              <h4 class="font-semibold text-slate-900">{{ section.title }}</h4>
              <el-tag size="small" :type="section.type" effect="plain">{{ section.count }}</el-tag>
            </div>
            <p class="mt-1 text-xs text-slate-500">{{ section.description }}</p>
          </div>

          <div v-if="section.items.length" class="space-y-2">
            <article
              v-for="item in section.items"
              :key="item.key"
              class="rounded border border-white bg-white p-3 shadow-sm"
            >
              <div class="flex items-start justify-between gap-2">
                <div>
                  <p class="text-sm font-semibold text-slate-900">{{ item.title }}</p>
                  <p v-if="item.subtitle" class="mt-1 text-xs text-slate-500">{{ item.subtitle }}</p>
                </div>
                <el-tag size="small" :type="priorityType(item.priority)" effect="plain">{{ item.priority }}</el-tag>
              </div>
              <p class="mt-2 text-sm text-slate-700">
                <span class="font-medium">下一步：</span>{{ item.nextAction }}
              </p>
              <p v-if="item.reason" class="mt-1 text-xs text-slate-500">
                <span class="font-medium">依据：</span>{{ item.reason }}
              </p>
              <div class="mt-2 flex flex-wrap gap-1">
                <el-tag v-if="item.owner" size="small" type="primary" effect="plain">{{ item.owner }}</el-tag>
                <el-tag v-if="item.partner" size="small" effect="plain">{{ item.partner }}</el-tag>
                <el-tag
                  v-for="focus in item.productFocus.slice(0, 4)"
                  :key="focus"
                  size="small"
                  type="info"
                  effect="plain"
                >
                  {{ focus }}
                </el-tag>
              </div>
              <el-button class="mt-2" size="small" type="primary" plain @click="go(item.path)">
                进入处理
              </el-button>
            </article>
          </div>

          <div v-else class="rounded border border-dashed border-slate-200 bg-white p-3 text-sm text-slate-500">
            暂无真实可推进数据。请先录入对应客户、报价、订单或反馈，不再用演示数据填充判断。
          </div>
        </section>
      </div>

      <section class="mt-4 rounded border border-blue-100 bg-blue-50/50 p-3">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h4 class="font-semibold text-slate-900">管理层今日判断摘要</h4>
            <p class="mt-1 text-sm text-slate-600">
              这里只保留能指导行动的问题：跟进谁、报价怎么推进、产品和 Partner 是否有风险、交付或反馈是否需要回流。
            </p>
          </div>
          <el-tag type="primary" effect="plain">内部可见</el-tag>
        </div>

        <div class="mt-3 grid gap-2 lg:grid-cols-3">
          <article
            v-for="brief in localizedBrief.slice(0, 6)"
            :key="brief.key"
            class="rounded border border-blue-100 bg-white p-3"
          >
            <div class="flex items-start justify-between gap-2">
              <h5 class="text-sm font-semibold text-slate-900">{{ brief.question }}</h5>
              <el-tag size="small" type="primary" effect="plain">{{ brief.owner }}</el-tag>
            </div>
            <p class="mt-2 text-sm text-slate-800">{{ brief.answer }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ brief.evidence }}</p>
            <p class="mt-1 text-xs text-slate-700">下一步：{{ brief.action }}</p>
            <div class="mt-2 flex flex-wrap gap-1">
              <el-tag
                v-for="asset in brief.assets.slice(0, 3)"
                :key="asset"
                size="small"
                type="info"
                effect="plain"
              >
                {{ asset }}
              </el-tag>
              <el-tag
                v-for="focus in brief.productFocus.slice(0, 4)"
                :key="focus"
                size="small"
                effect="plain"
              >
                {{ focus }}
              </el-tag>
            </div>
          </article>
        </div>

        <p v-if="!localizedBrief.length" class="mt-3 rounded border border-dashed border-blue-100 bg-white p-3 text-sm text-slate-500">
          暂无可用于管理层判断的真实经营记录。请优先补充真实报价结果、订单交付状态和反馈记录。
        </p>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { BusinessExecution } from '@/api/dashboard'

const props = defineProps<{
  data: BusinessExecution | null
}>()

const router = useRouter()

type ChainItem = {
  key: string
  title: string
  subtitle: string
  reason: string
  nextAction: string
  owner: string
  partner: string
  productFocus: string[]
  priority: string
  path: string
}

const syntheticPatterns = [/D8\./i, /demo/i, /sample/i, /dry-run/i, /mock/i, /rehearsal/i]

const allBusinessObjects = computed(() => {
  if (!props.data) return []
  return [
    ...props.data.account_lifecycle,
    ...props.data.opportunities,
    ...props.data.quotations,
    ...props.data.products,
    ...props.data.partners,
    ...props.data.delivery,
    ...(props.data.commercial_intelligence?.customer_value || []),
    ...(props.data.commercial_intelligence?.account_360 || []),
  ] as Array<Record<string, unknown>>
})

const hiddenSyntheticCount = computed(() => allBusinessObjects.value.filter(isSyntheticObject).length)

const realCounts = computed(() => ({
  accounts: realList(props.data?.account_lifecycle).length,
  opportunities: realList(props.data?.opportunities).length,
  quotes: realList(props.data?.quotations).length,
  delivery: realList(props.data?.delivery).length,
  partners: realList(props.data?.partners).length,
}))

const chainSections = computed(() => [
  {
    key: 'customer',
    title: '客户与机会',
    description: '先判断今天该推进哪个客户、机会或分群。',
    type: 'primary' as const,
    count: realCounts.value.accounts + realCounts.value.opportunities,
    items: [
      ...realList(props.data?.account_lifecycle).slice(0, 2).map(accountItem),
      ...realList(props.data?.opportunities).slice(0, 2).map(opportunityItem),
    ].slice(0, 3),
  },
  {
    key: 'quote',
    title: '报价与赢输',
    description: '沉淀报价经验，明确下一次报价该强调什么、避免什么。',
    type: 'warning' as const,
    count: realCounts.value.quotes + realList(props.data?.commercial_intelligence?.win_loss).length,
    items: [
      ...realList(props.data?.quotations).slice(0, 3).map(quoteItem),
      ...realList(props.data?.commercial_intelligence?.win_loss).slice(0, 2).map(winLossItem),
    ].slice(0, 3),
  },
  {
    key: 'product_partner',
    title: '产品与 Partner',
    description: '判断产品线是否被市场验证，以及 Partner 承接是否可靠。',
    type: 'success' as const,
    count: realList(props.data?.products).length + realCounts.value.partners,
    items: [
      ...realList(props.data?.products).slice(0, 2).map(productItem),
      ...realList(props.data?.partners).slice(0, 2).map(partnerItem),
    ].slice(0, 3),
  },
  {
    key: 'delivery_feedback',
    title: '交付与反馈',
    description: '把生产、物流、售后反馈回流到复购和 Market Response。',
    type: 'danger' as const,
    count: realCounts.value.delivery,
    items: realList(props.data?.delivery).slice(0, 3).map(deliveryItem),
  },
])

const localizedBrief = computed(() => {
  const summary = props.data?.commercial_intelligence?.executive_summary || {}
  const raw = Array.isArray(summary.management_brief) ? summary.management_brief : []
  return raw
    .filter((item) => !isSyntheticObject(item as Record<string, unknown>))
    .map((item, index) => {
      const row = item as Record<string, unknown>
      return {
        key: String(row.key || index),
        question: zhQuestion(String(row.question || '经营判断')),
        answer: zhText(String(row.answer || '暂无明确结论')),
        evidence: zhText(String(row.evidence || '等待更多真实业务记录')),
        action: zhText(String(row.recommended_action || '进入对应页面人工确认')),
        owner: zhOwner(String(row.owner || 'business owner')),
        assets: list(row.source_assets).map(zhAsset),
        productFocus: list(row.product_focus).map(zhProduct),
      }
    })
})

function go(path: string) {
  router.push(path || '/')
}

function realList<T extends Record<string, unknown>>(items?: T[] | null) {
  return (items || []).filter((item) => !isSyntheticObject(item))
}

function isSyntheticObject(item: Record<string, unknown>) {
  const fields = [
    item.customer_name,
    item.account_key,
    item.opportunity_name,
    item.quote_number,
    item.order_number,
    item.answer,
    item.evidence,
    item.reason,
    item.next_action,
    item.partner_focus,
  ]
  const text = fields
    .filter((value) => value !== null && value !== undefined)
    .map((value) => String(value))
    .join(' ')
  return syntheticPatterns.some((pattern) => pattern.test(text))
}

function accountItem(row: Record<string, unknown>): ChainItem {
  return {
    key: `account-${String(row.account_key || row.customer_name)}`,
    title: String(row.customer_name || '未命名客户'),
    subtitle: `阶段：${zhStatus(String(row.current_stage || '待判断'))}`,
    reason: zhText(String(row.decision_reason || row.next_action || '等待真实客户动作')),
    nextAction: zhText(String(row.next_action || '确认客户下一步动作')),
    owner: zhOwner(String(row.owner || 'account owner')),
    partner: String(row.partner_focus || ''),
    productFocus: list(row.product_focus).map(zhProduct),
    priority: String(row.priority || 'P2'),
    path: firstPath(row.active_paths) || '/companies',
  }
}

function opportunityItem(row: Record<string, unknown>): ChainItem {
  return {
    key: `opportunity-${String(row.id || row.opportunity_name)}`,
    title: String(row.opportunity_name || row.customer_or_segment || '未命名机会'),
    subtitle: `客户/分群：${String(row.customer_or_segment || '待确认')}`,
    reason: zhText(String(row.risk || row.competitive_signal || '等待机会判断')),
    nextAction: zhText(String(row.next_action || '补齐机会信息并判断是否报价')),
    owner: zhOwner(String(row.owner || 'sales owner')),
    partner: String(row.partner_focus || ''),
    productFocus: list(row.product_focus).map(zhProduct),
    priority: String(row.priority || 'P2'),
    path: String(row.path || '/growth-operations'),
  }
}

function quoteItem(row: Record<string, unknown>): ChainItem {
  return {
    key: `quote-${String(row.quote_id || row.quote_number)}`,
    title: `报价 ${String(row.quote_number || '未编号')}`,
    subtitle: String(row.customer_name || '客户待确认'),
    reason: zhText(String(row.learning_signal || row.outcome_signal || '等待报价结果沉淀')),
    nextAction: zhText(String(row.next_action || '人工跟进报价并记录赢输原因')),
    owner: '销售负责人',
    partner: '',
    productFocus: list(row.product_focus).map(zhProduct),
    priority: String((row.commercial_intelligence as Record<string, unknown> | undefined)?.priority || 'P2'),
    path: String(row.path || '/quotes'),
  }
}

function winLossItem(row: Record<string, unknown>): ChainItem {
  return {
    key: `winloss-${String(row.source_type || 'record')}-${String(row.source_id || row.customer || row.customer_name)}`,
    title: zhOutcome(String(row.outcome || 'still_active')),
    subtitle: String(row.customer || row.customer_name || '客户待确认'),
    reason: zhText(String(row.commercial_lesson || row.reason_category || '等待人工记录赢输原因')),
    nextAction: zhText(String(row.next_quote_guidance || '下次报价前复用本条经验')),
    owner: '销售负责人',
    partner: String(row.partner_focus || ''),
    productFocus: list(row.decision_factors).map(zhProduct),
    priority: String(row.outcome) === 'lost' ? 'P1' : 'P2',
    path: '/quotes',
  }
}

function productItem(row: Record<string, unknown>): ChainItem {
  return {
    key: `product-${String(row.partner_focus)}-${list(row.product_focus).join('-')}`,
    title: list(row.product_focus).map(zhProduct).join(' / ') || '产品线待确认',
    subtitle: String(row.partner_focus || 'Partner 待确认'),
    reason: zhText(String(row.validation_signal || row.risk || '等待市场验证')),
    nextAction: zhText(String(row.next_action || '补充产品验证和客户可见证据')),
    owner: '产品/市场负责人',
    partner: String(row.partner_focus || ''),
    productFocus: list(row.dimensions).map(zhProduct),
    priority: String((row.validation_context as Record<string, unknown> | undefined)?.priority || 'P2'),
    path: String(row.source_path || '/market-response'),
  }
}

function partnerItem(row: Record<string, unknown>): ChainItem {
  return {
    key: `partner-${String(row.partner_id || row.partner_name)}`,
    title: String(row.partner_name || 'Partner 待确认'),
    subtitle: `承接能力：${zhStatus(String(row.delivery_ability || row.readiness_level || '待评估'))}`,
    reason: zhText(String(row.risk_assessment || '等待 Partner 能力记录')),
    nextAction: zhText(String(row.next_action || '补齐 Partner 能力和交付证据')),
    owner: 'Partner 负责人',
    partner: String(row.partner_name || ''),
    productFocus: list(row.product_coverage).map(zhProduct),
    priority: String((row.capability_intelligence as Record<string, unknown> | undefined)?.investment_priority || 'P2'),
    path: String(row.path || '/partner-onboarding'),
  }
}

function deliveryItem(row: Record<string, unknown>): ChainItem {
  return {
    key: `delivery-${String(row.order_id || row.order_number)}`,
    title: `订单 ${String(row.order_number || '未编号')}`,
    subtitle: String(row.customer_name || '客户待确认'),
    reason: zhText(String(row.repeat_business_risk || row.production_signal || row.shipment_signal || '等待交付记录')),
    nextAction: zhText(String(row.next_action || '更新生产/物流状态并回流反馈')),
    owner: '交付负责人',
    partner: '',
    productFocus: [],
    priority: String(row.risk_level) === 'high' ? 'P1' : 'P2',
    path: String(row.path || '/orders'),
  }
}

function list(value: unknown) {
  return Array.isArray(value) ? value.map((item) => String(item)).filter(Boolean) : []
}

function firstPath(value: unknown) {
  return Array.isArray(value) && value.length ? String(value[0]) : ''
}

function priorityType(priority: string) {
  if (priority === 'P0') return 'danger'
  if (priority === 'P1') return 'warning'
  if (priority === 'P2') return 'primary'
  return 'info'
}

function zhQuestion(value: string) {
  const labels: Record<string, string> = {
    'Who is most worth following today?': '今天最值得跟进谁？',
    'What is most likely to convert?': '什么最可能转化？',
    'Which accounts look commercially healthiest without using cost or margin?': '哪些客户商业状态最健康？',
    'Why do we win?': '为什么能赢单？',
    'Why do we lose?': '为什么会丢单？',
    'Where will future revenue come from?': '未来收入可能来自哪里？',
    'Which partner deserves more operating attention?': '哪个 Partner 更值得投入？',
  }
  return labels[value] || zhText(value)
}

function zhOwner(value: string) {
  const labels: Record<string, string> = {
    'after-sales owner': '售后负责人',
    'product/market owner': '产品/市场负责人',
    'product owner': '产品负责人',
    'account owner': '客户负责人',
    'sales owner': '销售负责人',
    'business owner': '业务负责人',
    'partner owner': 'Partner 负责人',
  }
  return labels[value] || value || '业务负责人'
}

function zhAsset(value: string) {
  const labels: Record<string, string> = {
    'Account 360': '客户 360',
    'Customer Value Intelligence': '客户价值判断',
    'Revenue Forecast Intelligence': '收入预测',
    'Product-Market Fit Intelligence': '产品市场匹配',
    'Win/Loss Intelligence': '赢输经验',
    'Order Evidence': '订单证据',
    'Quote Learning': '报价经验',
    Opportunity: '机会',
    Quote: '报价',
    'Order Backlog': '订单交付池',
    'Partner Performance Intelligence': 'Partner 表现',
    'Quote Support': '报价支持',
    'Order Delivery': '订单交付',
    Feedback: '反馈',
  }
  return labels[value] || value
}

function zhStatus(value: string) {
  const labels: Record<string, string> = {
    conversion_ready: '可推进成交',
    pipeline_active: '项目推进中',
    delivery_risk: '交付风险',
    after_sales_attention: '售后需关注',
    blocked: '阻塞',
    nurture: '继续培育',
    active: '进行中',
    confirmed: '已确认',
    pending: '待确认',
    baseline_only: '仅有基础记录',
    not_evaluated: '待评估',
  }
  return labels[value] || value
}

function zhOutcome(value: string) {
  const labels: Record<string, string> = {
    won: '赢单经验',
    lost: '丢单复盘',
    no_response: '客户未回复',
    deferred: '客户延期',
    still_active: '仍在推进',
  }
  return labels[value] || '报价结果'
}

function zhProduct(value: string) {
  const labels: Record<string, string> = {
    lifting_systems: '升降系统',
    'lifting systems': '升降系统',
    lifting_system: '升降系统',
    lifting_frame: '升降桌架',
    desk_frames: '升降桌架',
    'desk frames': '升降桌架',
    desk_frame: '升降桌架',
    desk_legs: '桌腿',
    'desk legs': '桌腿',
    lifting_columns: '升降柱',
    'lifting columns': '升降柱',
    lifting_column: '升降柱',
    'heavy-duty supply': '重载供应',
    heavy_duty_supply: '重载供应',
    education_furniture: '教育家具',
    'education furniture': '教育家具',
    'school desks/chairs': '学校桌椅',
    school_desks_chairs: '学校桌椅',
    project_furniture: '项目制家具',
    'project furniture': '项目制家具',
    load: '承重',
    stability: '稳定性',
    noise: '噪音',
    delivery: '交付',
    installation: '安装',
    packaging: '包装',
    warranty: '质保',
    certification: '认证',
    test_cycle: '测试周期',
    project_demand: '项目需求',
  }
  return labels[value] || value.replaceAll('_', ' ')
}

function zhText(value: string) {
  const replacements: Array<[RegExp, string]> = [
    [/No priority account has enough commercial evidence yet\./gi, '暂无足够证据判断优先客户。'],
    [/No product line has enough conversion evidence yet\./gi, '暂无足够证据判断高转化产品线。'],
    [/No commercial quality leader is ready yet\./gi, '暂无明确商业健康客户。'],
    [/No won reason has been captured yet\./gi, '尚未记录赢单原因。'],
    [/No lost reason has been captured yet\./gi, '尚未记录丢单原因。'],
    [/No forecastable revenue source is ready yet\./gi, '尚无可预测收入来源。'],
    [/HOSUN strategic account/gi, 'HOSUN 重点客户'],
    [/JOOBOO school desks\/chairs project/gi, 'JOOBOO 学校桌椅项目'],
    [/Future partner pilot quote/gi, '未来 Partner 试点报价'],
    [/Account 360 shows repeat motion and active quote learning\./gi, '客户 360 显示已有复购动作和报价经验。'],
    [/Education furniture demand is tied to school procurement timing\./gi, '教育家具需求与学校采购周期相关。'],
    [/Open opportunity and quote backlog are available\./gi, '已有开放机会和报价储备。'],
    [/Review feedback before repeat outreach\./gi, '先复核反馈，再进行复购触达。'],
    [/Use project furniture proof in the next quote review\./gi, '下次报价复核时使用项目制家具证据。'],
    [/Review revenue forecast before allocating partner capacity\./gi, '分配 Partner 产能前先复核收入预测。'],
    [/Review/gi, '复核'],
    [/Capture/gi, '记录'],
    [/before/gi, '之后再'],
    [/customer-visible/gi, '客户可见'],
    [/repeat business/gi, '复购'],
    [/feedback/gi, '反馈'],
    [/quote/gi, '报价'],
    [/order/gi, '订单'],
    [/delivery/gi, '交付'],
    [/after-sales/gi, '售后'],
    [/pilot/gi, '试点'],
    [/risk/gi, '风险'],
    [/partner/gi, 'Partner'],
    [/product\/market/gi, '产品/市场'],
    [/owner/gi, '负责人'],
    [/staging/gi, 'staging'],
    [/dry-run/gi, '本地演练'],
  ]
  return replacements.reduce((text, [pattern, replacement]) => text.replace(pattern, replacement), value)
}
</script>
