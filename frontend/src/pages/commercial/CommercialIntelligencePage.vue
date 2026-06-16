<template>
  <div class="space-y-5" v-loading="loading">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">商业智能工作台</h2>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          把 Win/Loss、客户价值、Partner 绩效、产品市场匹配、收入预测和 Account 360 组织成管理层可查询的商业经验库。
        </p>
      </div>
      <div class="flex gap-2">
        <el-button size="small" type="primary" plain @click="go('/')">返回行动看板</el-button>
        <el-button size="small" :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="内部商业智能层：不自动发送外部消息、不改报价或订单状态、不暴露成本、利润、供应商私密信息、raw token 或客户不可见字段。"
    />
    <el-alert v-if="error" type="error" :closable="false" :title="error" />

    <template v-if="data">
      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-900">管理层今天能回答什么</h3>
            <p class="mt-1 text-sm text-slate-600">
              这些答案来自真实业务对象的只读聚合，可继续跳转到客户、报价、订单、Market Response 或 Partner 接入页面处理。
            </p>
          </div>
          <div class="flex flex-wrap gap-1">
            <el-tag type="success" effect="plain">加权收入 {{ money(snapshot.total_weighted_revenue) }}</el-tag>
            <el-tag type="primary" effect="plain">预测质量 {{ snapshot.forecast_quality_score ?? 0 }}/100</el-tag>
            <el-tag type="warning" effect="plain">风险收入 {{ money(snapshot.at_risk_weighted_amount) }}</el-tag>
          </div>
        </div>

        <div class="grid gap-3 lg:grid-cols-3">
          <div
            v-for="section in managementSections"
            :key="section.key"
            class="rounded border border-slate-100 bg-slate-50 p-3"
          >
            <div class="mb-2 flex items-start justify-between gap-2">
              <div>
                <h4 class="text-sm font-semibold text-slate-900">{{ section.title }}</h4>
                <p class="mt-1 text-xs text-slate-500">{{ section.description }}</p>
              </div>
              <el-tag size="small" effect="plain">{{ section.items.length }}</el-tag>
            </div>
            <div v-for="item in section.items.slice(0, 3)" :key="rowKey(item)" class="mb-3 last:mb-0">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" :type="priorityType(String(item.priority || section.priority))" effect="plain">
                  {{ item.priority || section.priority }}
                </el-tag>
                <el-tag v-if="item.source_asset" size="small" type="info" effect="plain">{{ item.source_asset }}</el-tag>
              </div>
              <p class="mt-1 text-sm font-medium text-slate-800">{{ item.title || item.customer_name || item.name || item.partner_name || item.product_family || '商业对象' }}</p>
              <p class="mt-1 text-xs text-slate-600">{{ item.reason || item.next_action || item.management_answer || item.commercial_lesson || item.risk_reason || '等待更多商业证据。' }}</p>
              <el-button v-if="item.path" class="mt-1" size="small" link type="primary" @click="go(String(item.path))">进入来源</el-button>
            </div>
            <p v-if="!section.items.length" class="text-sm text-slate-500">暂无可用商业证据。</p>
          </div>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-900">六类商业资产覆盖</h3>
            <p class="mt-1 text-sm text-slate-600">每个资产都回答一个管理问题，避免只展示分散后台数据。</p>
          </div>
          <el-tag type="primary" effect="plain">商业资产 {{ data.summary.commercial_intelligence_items }}</el-tag>
        </div>
        <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <div v-for="asset in assetMap" :key="String(asset.asset)" class="rounded border border-slate-100 p-3">
            <div class="flex items-start justify-between gap-2">
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ asset.asset }}</p>
                <p class="mt-1 text-xs text-slate-600">{{ asset.answers }}</p>
              </div>
              <el-tag size="small" effect="plain">{{ asset.items ?? 0 }}</el-tag>
            </div>
            <el-button class="mt-2" size="small" link type="primary" @click="go(String(asset.path || '/'))">查看业务入口</el-button>
          </div>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-900">商业经验库查询</h3>
            <p class="mt-1 text-sm text-slate-600">
              按 partner、产品线、购买因素或客户查看可复用经验：为什么赢输、哪些因素影响成交、哪些账户需要下一次商业动作。
            </p>
          </div>
          <div class="flex flex-wrap gap-1">
            <el-tag type="primary" effect="plain">原因簇 {{ winLossReasonClusters.length }}</el-tag>
            <el-tag type="success" effect="plain">PMF 购买因素 {{ pmfBuyingFactors.length }}</el-tag>
            <el-tag type="warning" effect="plain">推荐账户 {{ accountRecommendations.length }}</el-tag>
            <el-tag type="info" effect="plain">客户价值 {{ customerValueRows.length }}</el-tag>
            <el-tag type="info" effect="plain">Partner 绩效 {{ partnerPerformanceRows.length }}</el-tag>
            <el-tag type="info" effect="plain">收入预测 {{ revenueForecastRows.length }}</el-tag>
          </div>
        </div>

        <div class="mb-3 grid gap-2 md:grid-cols-4">
          <el-select v-model="selectedPartner" clearable filterable placeholder="Partner">
            <el-option v-for="item in partnerOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="selectedProduct" clearable filterable placeholder="产品线">
            <el-option v-for="item in productOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="selectedFactor" clearable filterable placeholder="购买因素">
            <el-option v-for="item in factorOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="selectedCustomer" clearable filterable placeholder="客户">
            <el-option v-for="item in customerOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </div>

        <div class="grid gap-3 xl:grid-cols-4">
          <div class="rounded border border-slate-100 bg-slate-50 p-3">
            <h4 class="text-sm font-semibold text-slate-900">为什么赢 / 输</h4>
            <p class="mt-1 text-xs text-slate-500">来自 Win/Loss reason clusters 和客户决策因素。</p>
            <div v-for="item in filteredReasonClusters.slice(0, 4)" :key="rowKey(item)" class="mt-2 rounded bg-white p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" type="info" effect="plain">{{ primaryText(item, ['reason_category', 'factor', 'partner_name', 'partner_focus', 'product_focus'], '原因') }}</el-tag>
                <el-tag size="small" type="success" effect="plain">赢 {{ item.won ?? item.win_count ?? 0 }}</el-tag>
                <el-tag size="small" type="danger" effect="plain">输 {{ item.lost ?? item.loss_count ?? 0 }}</el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-600">{{ primaryText(item, ['next_quote_guidance', 'sample_lessons', 'reason'], '复盘原因后再复用到下一次报价。') }}</p>
            </div>
            <p v-if="!filteredReasonClusters.length" class="mt-2 text-sm text-slate-500">当前筛选下暂无赢输原因。</p>
          </div>

          <div class="rounded border border-slate-100 bg-slate-50 p-3">
            <h4 class="text-sm font-semibold text-slate-900">购买因素证据</h4>
            <p class="mt-1 text-xs text-slate-500">来自 PMF validated buying factors 和产品线证据。</p>
            <div v-for="item in filteredBuyingFactors.slice(0, 4)" :key="rowKey(item)" class="mt-2 rounded bg-white p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" type="primary" effect="plain">{{ primaryText(item, ['factor', 'dimension', 'buying_factor', 'product_focus'], '购买因素') }}</el-tag>
                <el-tag size="small" effect="plain">{{ primaryText(item, ['partner_focus', 'partner', 'partner_name'], 'multi-partner') }}</el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-600">
                证据 {{ item.evidence_count ?? item.evidence ?? 0 }} / 赢 {{ item.wins ?? 0 }} / 输 {{ item.losses ?? 0 }} / 反馈 {{ item.feedback ?? 0 }}
              </p>
              <p class="mt-1 text-xs text-slate-500">{{ primaryText(item, ['next_action', 'management_answer'], '确认该因素是否应进入报价话术和客户可见材料。') }}</p>
            </div>
            <p v-if="!filteredBuyingFactors.length" class="mt-2 text-sm text-slate-500">当前筛选下暂无购买因素证据。</p>
          </div>

          <div class="rounded border border-slate-100 bg-slate-50 p-3">
            <h4 class="text-sm font-semibold text-slate-900">下一批客户动作</h4>
            <p class="mt-1 text-xs text-slate-500">来自 Account 360 推荐账户和下一商业动作。</p>
            <div v-for="item in filteredAccounts.slice(0, 4)" :key="rowKey(item)" class="mt-2 rounded bg-white p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" :type="priorityType(String(item.priority || 'P2'))" effect="plain">{{ item.priority || 'P2' }}</el-tag>
                <el-tag size="small" effect="plain">{{ item.current_stage || item.relationship_depth || 'account' }}</el-tag>
              </div>
              <p class="mt-1 text-sm font-medium text-slate-800">{{ item.customer_name || item.account_key }}</p>
              <p class="mt-1 text-xs text-slate-600">{{ nextMotion(item).next_action || item.next_action || '查看 Account 360 后选择下一步。' }}</p>
              <el-button class="mt-1" size="small" link type="primary" @click="go(String(item.path || '/growth-operations'))">打开账户</el-button>
            </div>
            <p v-if="!filteredAccounts.length" class="mt-2 text-sm text-slate-500">当前筛选下暂无推荐账户。</p>
          </div>

          <div class="rounded border border-slate-100 bg-slate-50 p-3">
            <h4 class="text-sm font-semibold text-slate-900">下一次报价可复用</h4>
            <p class="mt-1 text-xs text-slate-500">把赢输经验转成报价、Campaign 和产品话术输入。</p>
            <div v-for="item in filteredDecisionFactors.slice(0, 4)" :key="rowKey(item)" class="mt-2 rounded bg-white p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" type="warning" effect="plain">{{ primaryText(item, ['factor', 'decision_factor', 'reason_category'], '决策因素') }}</el-tag>
                <el-tag size="small" effect="plain">{{ primaryText(item, ['product_focus', 'product', 'product_family'], '产品线') }}</el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-600">{{ primaryText(item, ['next_quote_guidance', 'management_answer', 'commercial_lesson'], '复用前先确认客户语境和产品证据。') }}</p>
            </div>
            <p v-if="!filteredDecisionFactors.length" class="mt-2 text-sm text-slate-500">当前筛选下暂无报价经验。</p>
          </div>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-900">商业资产明细</h3>
            <p class="mt-1 text-sm text-slate-600">按资产类型查看专用商业智能 API 产出的经营证据，继续处理时跳转到原始业务对象。</p>
          </div>
          <el-tag type="info" effect="plain">{{ activeAssetLabel }}</el-tag>
        </div>
        <el-tabs v-model="activeAsset">
          <el-tab-pane v-for="asset in assetSections" :key="asset.key" :label="asset.label" :name="asset.key">
            <el-table :data="asset.items.slice(0, 8)" size="small" border :empty-text="`${asset.label} 暂无数据`">
              <el-table-column label="对象" min-width="220">
                <template #default="{ row }">
                  <div class="font-medium text-slate-800">{{ row.title }}</div>
                  <div class="mt-1 flex flex-wrap gap-1">
                    <el-tag v-for="tag in row.tags.slice(0, 4)" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="商业判断" min-width="360">
                <template #default="{ row }">
                  <p class="text-sm text-slate-700">{{ row.reason }}</p>
                  <p class="mt-1 text-xs text-slate-500">{{ row.nextAction }}</p>
                </template>
              </el-table-column>
              <el-table-column label="入口" width="120">
                <template #default="{ row }">
                  <el-button size="small" link type="primary" @click="go(row.path)">打开</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </section>
    </template>

    <div v-else-if="!loading" class="rounded border border-slate-200 bg-white p-4 text-sm text-slate-500">
      暂无商业智能数据。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  fetchAccount360Intelligence,
  fetchBusinessExecution,
  fetchCustomerValueIntelligence,
  fetchPartnerPerformanceIntelligence,
  fetchProductMarketFitIntelligence,
  fetchRevenueForecastIntelligence,
  fetchWinLossIntelligenceDashboard,
  type Account360Intelligence,
  type BusinessExecution,
  type CustomerValueIntelligence,
  type PartnerPerformanceIntelligence,
  type ProductMarketFitIntelligence,
  type RevenueForecastIntelligence,
  type WinLossIntelligenceDashboard,
} from '@/api/dashboard'

type Row = Record<string, unknown>

const router = useRouter()
const loading = ref(false)
const error = ref('')
const data = ref<BusinessExecution | null>(null)
const winLossDashboard = ref<WinLossIntelligenceDashboard | null>(null)
const productMarketFit = ref<ProductMarketFitIntelligence | null>(null)
const account360 = ref<Account360Intelligence | null>(null)
const customerValue = ref<CustomerValueIntelligence | null>(null)
const partnerPerformance = ref<PartnerPerformanceIntelligence | null>(null)
const revenueForecast = ref<RevenueForecastIntelligence | null>(null)
const activeAsset = ref('account360')
const selectedPartner = ref('')
const selectedProduct = ref('')
const selectedFactor = ref('')
const selectedCustomer = ref('')

const commercial = computed(() => data.value?.commercial_intelligence)
const executiveSummary = computed(() => asRecord(commercial.value?.executive_summary))
const questions = computed(() => asRecord(executiveSummary.value.management_questions))
const snapshot = computed(() => asRecord(executiveSummary.value.commercial_snapshot))
const assetMap = computed(() => asList(executiveSummary.value.asset_map))
const winLossReasonClusters = computed(() => [
  ...asList(winLossDashboard.value?.reason_clusters),
  ...asList(winLossDashboard.value?.partner_rollup),
  ...asList(winLossDashboard.value?.product_rollup),
])
const winLossDecisionFactors = computed(() => asList(winLossDashboard.value?.decision_factor_rows))
const pmfBuyingFactors = computed(() => [
  ...asList(productMarketFit.value?.validated_buying_factors),
  ...asList(productMarketFit.value?.top_product_lines).flatMap((item) => asList(item.buying_factors_ranked)),
  ...asList(productMarketFit.value?.items).flatMap((item) => asList(item.buying_factors_ranked)),
])
const accountRecommendations = computed(() => [
  ...asList(account360.value?.recommended_accounts),
  ...asList(account360.value?.repeat_or_referral_accounts),
  ...asList(account360.value?.reactivation_accounts),
])
const customerValueRows = computed(() => [
  ...asList(customerValue.value?.commercial_quality_leaders),
  ...asList(customerValue.value?.items),
])
const partnerPerformanceRows = computed(() => [
  ...asList(partnerPerformance.value?.top_investment_candidates),
  ...asList(partnerPerformance.value?.quote_allocation_candidates),
  ...asList(partnerPerformance.value?.pilot_candidates),
  ...asList(partnerPerformance.value?.items),
])
const revenueForecastRows = computed(() => [
  ...asList(revenueForecast.value?.high_probability_projects),
  ...asList(revenueForecast.value?.high_risk_projects),
  ...asList(revenueForecast.value?.committed_backlog),
  ...asList(revenueForecast.value?.forecastable_revenue),
  ...asList(revenueForecast.value?.forecast_items),
])
const partnerOptions = computed(() =>
  uniqueText([
    ...asList(productMarketFit.value?.items).flatMap((item) => [item.partner_focus, item.partner, item.partner_name]),
    ...asList(winLossDashboard.value?.partner_rollup).flatMap((item) => [item.partner_focus, item.partner, item.partner_name]),
    ...asList(account360.value?.items).flatMap((item) => (Array.isArray(item.partner_focus) ? item.partner_focus : [item.partner_focus])),
    ...partnerPerformanceRows.value.flatMap((item) => [item.partner_focus, item.partner, item.partner_name]),
    ...revenueForecastRows.value.flatMap((item) => [item.partner_focus, item.partner, item.partner_name]),
  ]),
)
const productOptions = computed(() =>
  uniqueText([
    ...asList(productMarketFit.value?.items).flatMap((item) => (Array.isArray(item.product_focus) ? item.product_focus : [item.product_focus, item.product_family, item.product])),
    ...asList(winLossDashboard.value?.product_rollup).flatMap((item) => [item.product_focus, item.product_family, item.product]),
    ...asList(account360.value?.items).flatMap((item) => (Array.isArray(item.product_focus) ? item.product_focus : [item.product_focus])),
    ...partnerPerformanceRows.value.flatMap((item) => (Array.isArray(item.product_coverage) ? item.product_coverage : [item.product_focus, item.product_family])),
    ...revenueForecastRows.value.flatMap((item) => (Array.isArray(item.product_focus) ? item.product_focus : [item.product_family, item.product_focus])),
  ]),
)
const factorOptions = computed(() =>
  uniqueText([
    ...winLossDecisionFactors.value.flatMap((item) => [item.factor, item.decision_factor, item.reason_category]),
    ...pmfBuyingFactors.value.flatMap((item) => [item.factor, item.dimension, item.buying_factor]),
    ...asList(productMarketFit.value?.items).flatMap((item) => (Array.isArray(item.dimensions) ? item.dimensions : [])),
  ]),
)
const customerOptions = computed(() =>
  uniqueText([
    ...asList(account360.value?.items).flatMap((item) => [item.customer_name, item.account_key]),
    ...asList(winLossDashboard.value?.items).flatMap((item) => [item.customer, item.customer_name]),
    ...customerValueRows.value.flatMap((item) => [item.customer_name, item.account_key]),
    ...revenueForecastRows.value.flatMap((item) => [item.customer_name, item.customer_or_segment, item.account_key]),
  ]),
)
const filteredReasonClusters = computed(() => filterExperienceRows(winLossReasonClusters.value))
const filteredBuyingFactors = computed(() => filterExperienceRows(pmfBuyingFactors.value))
const filteredAccounts = computed(() => filterExperienceRows(accountRecommendations.value))
const filteredDecisionFactors = computed(() => filterExperienceRows(winLossDecisionFactors.value))

const managementSections = computed(() => [
  {
    key: 'follow',
    title: '谁最值得跟进',
    description: '按 Account 360、客户价值和下一商业动作判断。',
    priority: 'P1',
    items: asList(questions.value.who_to_follow_today),
  },
  {
    key: 'convert',
    title: '什么最容易成交',
    description: '按 PMF、订单证据、赢输原因和购买因素判断。',
    priority: 'P1',
    items: asList(questions.value.what_converts),
  },
  {
    key: 'revenue',
    title: '未来收入来自哪里',
    description: '按机会、报价、订单 backlog 的加权预测判断。',
    priority: 'P1',
    items: asList(questions.value.future_revenue_from),
  },
  {
    key: 'partner',
    title: '哪个 Partner 值得投入',
    description: '按报价支持、赢单、订单、交付和反馈判断。',
    priority: 'P2',
    items: asList(questions.value.which_partner_to_invest),
  },
  {
    key: 'winloss',
    title: '为什么赢 / 为什么输',
    description: '把客户决策因素沉淀为下一次报价和 Campaign 的经验。',
    priority: 'P2',
    items: [...asList(questions.value.why_we_win), ...asList(questions.value.why_we_lose)],
  },
  {
    key: 'quality',
    title: '什么是健康商业价值',
    description: '不用成本或利润字段，用成交、复购、pipeline 和服务负担判断。',
    priority: 'P2',
    items: asList(questions.value.what_is_commercially_healthy),
  },
])

const assetSections = computed(() => [
  {
    key: 'account360',
    label: 'Account 360',
    items: asList(commercial.value?.account_360).map((item) => ({
      title: String(item.customer_name || item.account_key || '客户账户'),
      tags: textList([item.current_stage, item.priority, firstText(item.partner_focus), ...(Array.isArray(item.product_focus) ? item.product_focus : [])]),
      reason: String(item.decision_reason || item.repeat_business_signal || '客户商业档案已聚合。'),
      nextAction: String(item.next_action || '查看客户视角完整商业档案。'),
      path: String(item.path || firstText(item.active_paths) || '/growth-operations'),
    })),
  },
  {
    key: 'pmf',
    label: 'Product-Market Fit',
    items: asList(commercial.value?.product_market_fit).map((item) => ({
      title: `${item.partner_focus || 'future partner'} / ${textList(item.product_focus).join(' / ') || 'product family'}`,
      tags: textList([item.fit_status, ...(Array.isArray(item.purchase_factors) ? item.purchase_factors : [])]),
      reason: String(item.commercial_question || '产品市场证据已聚合。'),
      nextAction: String(item.next_action || '复核购买因素、项目经验和客户反馈。'),
      path: String(item.path || item.source_path || '/market-response'),
    })),
  },
  {
    key: 'partner',
    label: 'Partner Performance',
    items: uniqueRows([...partnerPerformanceRows.value, ...asList(commercial.value?.partner_performance)]).map((item) => ({
      title: String(item.partner_name || item.partner_focus || 'Partner'),
      tags: textList([item.investment_priority, item.allocation_fit, item.pilot_fit, ...(Array.isArray(item.product_coverage) ? item.product_coverage : [])]),
      reason: `报价支持 ${item.quote_support_count ?? 0}，赢单率 ${percent(item.win_rate)}，订单额 ${money(item.order_amount)}。`,
      nextAction: String(item.next_allocation_action || item.next_action || '查看 Partner 绩效证据。'),
      path: String(item.path || '/partner-onboarding'),
    })),
  },
  {
    key: 'winloss',
    label: 'Win/Loss',
    items: asList(commercial.value?.win_loss).map((item) => ({
      title: String(item.customer || item.quote_number || item.opportunity_name || '商业经验'),
      tags: textList([item.outcome, item.reason_category, ...(Array.isArray(item.decision_factors) ? item.decision_factors : [])]),
      reason: String(item.commercial_lesson || item.won_reason || item.lost_reason || '成交/丢单原因待补充。'),
      nextAction: String(item.next_quote_guidance || '把经验复用到下一次报价。'),
      path: String(item.path || '/quotes'),
    })),
  },
  {
    key: 'customerValue',
    label: '客户价值',
    items: uniqueRows([...customerValueRows.value, ...asList(commercial.value?.customer_value)]).map((item) => ({
      title: String(item.customer_name || '客户'),
      tags: textList([item.value_tier, item.priority, item.future_revenue_signal, asRecord(item.commercial_quality).tier]),
      reason: `报价 ${money(item.historical_quote_amount)}，成交 ${money(item.won_order_amount)}，pipeline ${money(item.weighted_pipeline_amount)}。`,
      nextAction: String(item.next_action || item.recommended_reason || '按客户价值决定跟进深度。'),
      path: String(item.path || '/companies'),
    })),
  },
  {
    key: 'forecast',
    label: '收入预测',
    items: uniqueRows([
      ...revenueForecastRows.value,
      ...asList(asRecord(commercial.value?.revenue_forecast).high_probability_projects),
    ]).map((item) => ({
      title: String(item.name || item.customer_name || item.source_type || '预测项目'),
      tags: textList([item.source_type, item.risk_level, item.forecast_confidence, item.revenue_bucket]),
      reason: `概率 ${item.probability ?? 0}%，加权金额 ${money(item.weighted_amount)}。`,
      nextAction: String(item.next_action || '保持人工跟进和预测输入更新。'),
      path: String(item.path || '/growth-operations'),
    })),
  },
])

const activeAssetLabel = computed(() => assetSections.value.find((item) => item.key === activeAsset.value)?.label || '商业资产')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [businessExecution, winLoss, pmf, accounts, customers, partners, forecast] = await Promise.all([
      fetchBusinessExecution(),
      fetchWinLossIntelligenceDashboard(120),
      fetchProductMarketFitIntelligence(80),
      fetchAccount360Intelligence(80),
      fetchCustomerValueIntelligence(80),
      fetchPartnerPerformanceIntelligence(80),
      fetchRevenueForecastIntelligence(120),
    ])
    data.value = businessExecution
    winLossDashboard.value = winLoss
    productMarketFit.value = pmf
    account360.value = accounts
    customerValue.value = customers
    partnerPerformance.value = partners
    revenueForecast.value = forecast
  } catch (err) {
    error.value = err instanceof Error ? err.message : '商业智能数据加载失败'
  } finally {
    loading.value = false
  }
}

function go(path: string) {
  router.push(path)
}

function asRecord(value: unknown): Row {
  return value && typeof value === 'object' && !Array.isArray(value) ? (value as Row) : {}
}

function asList(value: unknown): Row[] {
  return Array.isArray(value) ? (value.filter((item) => item && typeof item === 'object') as Row[]) : []
}

function firstText(value: unknown) {
  if (Array.isArray(value)) return value.length ? String(value[0]) : ''
  return value ? String(value) : ''
}

function primaryText(row: Row, keys: string[], fallback: string) {
  for (const key of keys) {
    const value = row[key]
    if (Array.isArray(value) && value.length) return value.map((item) => String(item)).join(' / ')
    if (value !== null && value !== undefined && String(value).trim()) return String(value)
  }
  return fallback
}

function textList(value: unknown) {
  const values = Array.isArray(value) ? value : [value]
  return values.filter((item) => item !== null && item !== undefined && String(item).trim()).map((item) => String(item))
}

function uniqueText(values: unknown[]) {
  return [...new Set(textList(values))].sort((left, right) => left.localeCompare(right))
}

function uniqueRows(rows: Row[]) {
  const seen = new Set<string>()
  return rows.filter((row) => {
    const key = rowKey(row)
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function rowSearchText(row: Row) {
  return JSON.stringify(row).toLowerCase()
}

function includesFilter(row: Row, filter: string) {
  return !filter || rowSearchText(row).includes(filter.toLowerCase())
}

function filterExperienceRows(rows: Row[]) {
  return rows.filter(
    (row) =>
      includesFilter(row, selectedPartner.value) &&
      includesFilter(row, selectedProduct.value) &&
      includesFilter(row, selectedFactor.value) &&
      includesFilter(row, selectedCustomer.value),
  )
}

function nextMotion(item: Row) {
  return asRecord(item.next_commercial_motion)
}

function asNumber(value: unknown) {
  const number = Number(value ?? 0)
  return Number.isFinite(number) ? number : 0
}

function money(value: unknown) {
  return `$${asNumber(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
}

function percent(value: unknown) {
  return `${Math.round(asNumber(value) * 100)}%`
}

function rowKey(row: Row) {
  return String(row.path || row.title || row.customer_name || row.name || row.partner_name || JSON.stringify(row).slice(0, 80))
}

function priorityType(priority: string) {
  if (priority === 'P0') return 'danger'
  if (priority === 'P1') return 'warning'
  if (priority === 'P2') return 'primary'
  return 'info'
}

onMounted(load)
</script>
