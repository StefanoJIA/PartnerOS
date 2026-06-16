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
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-900">商业资产明细</h3>
            <p class="mt-1 text-sm text-slate-600">按资产类型查看前 8 条可用经营证据，继续处理时跳转到原始业务对象。</p>
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
import { fetchBusinessExecution, type BusinessExecution } from '@/api/dashboard'

type Row = Record<string, unknown>

const router = useRouter()
const loading = ref(false)
const error = ref('')
const data = ref<BusinessExecution | null>(null)
const activeAsset = ref('account360')

const commercial = computed(() => data.value?.commercial_intelligence)
const executiveSummary = computed(() => asRecord(commercial.value?.executive_summary))
const questions = computed(() => asRecord(executiveSummary.value.management_questions))
const snapshot = computed(() => asRecord(executiveSummary.value.commercial_snapshot))
const assetMap = computed(() => asList(executiveSummary.value.asset_map))

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
    items: asList(commercial.value?.partner_performance).map((item) => ({
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
    items: asList(commercial.value?.customer_value).map((item) => ({
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
    items: asList(asRecord(commercial.value?.revenue_forecast).high_probability_projects).map((item) => ({
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
    data.value = await fetchBusinessExecution()
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

function textList(value: unknown) {
  const values = Array.isArray(value) ? value : [value]
  return values.filter((item) => item !== null && item !== undefined && String(item).trim()).map((item) => String(item))
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
