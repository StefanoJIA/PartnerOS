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
  'Read-only demo guide. It stays at READY_FOR_STAGING_HANDOFF and does not enter D9, validate staging, notify customers or suppliers, send email/webhooks, call carriers, or expose token/cost/margin/private-note fields.'

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
    label: 'Customer development',
    value: 'Brand + project intake',
    detail: 'Start with a customer need, target brand direction, and project context before proposing a product line.',
    route: '/leads',
  },
  {
    key: 'interest',
    label: 'Product adaptation',
    value: `${market.value?.summary.feedback_ticket_count ?? 0} feedback / ${market.value?.summary.market_signal_count ?? 0} market notes`,
    detail: 'Customer feedback, quote lines, order demand, and market notes show which product line fits the opportunity.',
    route: '/market-intelligence',
  },
  {
    key: 'quote',
    label: 'Quote',
    value: `${market.value?.summary.quote_count ?? 0} quotes`,
    detail: 'Quotes remain manually prepared and safety-gated; PartnerOS does not auto-send quotes.',
    route: '/quotes',
  },
  {
    key: 'order',
    label: 'Order',
    value: `${portal.value?.recent_customer_visible_orders.total ?? 0} customer-visible orders`,
    detail: 'Confirmed orders become the operating source of truth for customer tracking.',
    route: '/orders',
  },
  {
    key: 'partner',
    label: 'Partner split',
    value: `${portal.value?.multi_partner_flow_readiness.split_count ?? 0} splits across ${portal.value?.multi_partner_flow_readiness.partners_with_orders ?? 0} partners`,
    detail: 'HOSUN, JOOBOO, and future partners are peer manufacturing partners, not privileged platform defaults.',
    route: '/partner-operations',
  },
  {
    key: 'production',
    label: 'Production',
    value: `${portal.value?.customer_snapshot_readiness.production_visible_count ?? 0} orders with production visibility`,
    detail: 'Milestones are operator-maintained and customer-visible only through whitelisted summaries.',
    route: '/portal-integration',
  },
  {
    key: 'shipment',
    label: 'Shipment',
    value: `${portal.value?.shipment_readiness.total_count ?? 0} shipment plans`,
    detail: 'Logistics plans are manual; no carrier API, webhook, or automatic shipped/delivered mutation.',
    route: '/portal-integration',
  },
  {
    key: 'portal',
    label: 'Portal',
    value: `${portal.value?.customer_snapshot_readiness.snapshot_count ?? 0} customer snapshots`,
    detail: 'Customer Portal reads whitelisted products, orders, production, shipment, resources, and feedback status.',
    route: '/portal-integration',
  },
  {
    key: 'feedback',
    label: 'Feedback',
    value: `${portal.value?.feedback_operations.open_count ?? 0} open tickets`,
    detail: 'Feedback is triaged internally without auto-replies or SLA promises.',
    route: '/feedback-tickets',
  },
  {
    key: 'response',
    label: 'Market response',
    value: `${market.value?.summary.recommendation_count ?? 0} recommendations`,
    detail: 'Operators review signals before changing product focus, partner playbooks, or outreach.',
    route: '/market-intelligence',
  },
])

const storyLine = computed(() => [
  'Use PartnerOS to qualify a customer project, map it to the right partner product line, and keep the operator workflow connected after the quote becomes an order.',
  'The customer-facing Portal remains a filtered bridge: customers can inspect product, order, production, shipment, resource, and feedback status without seeing internal operating data.',
  'Market Response closes the loop by turning actual orders, delays, logistics risk, and feedback into human-reviewed product and partner priorities.',
])

const scenarioCards = computed(() => [
  {
    title: 'HOSUN lifting systems',
    partner: hosunPartner.value?.partner_name || 'HOSUN',
    focus: 'Desk frames, desk legs, lifting columns, and heavy-duty lifting projects',
    story:
      'The operator starts from adjustable workstation demand, prepares the quote, splits confirmed order lines to HOSUN, tracks production readiness, plans shipment, and watches logistics/feedback signals for the next market response.',
    route: { name: 'market', query: { focus_category: 'lifting_columns' } },
  },
  {
    title: 'JOOBOO education furniture',
    partner: secondaryPartner.value?.partner_name || 'JOOBOO / future partner',
    focus: 'Education furniture and project furniture programs',
    story:
      'The same operating loop works for classroom and project furniture: match product requirements, quote the program, split partner work, expose customer-safe delivery status, and convert feedback into partner focus.',
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
      .join('; ') || 'Watchlist category for operator review',
  })),
)

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
    error.value = formatApiError(e, 'Failed to load demo scenario.')
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

function focusLabel(key: string) {
  return focusLabels[key] || key
}

onMounted(load)
</script>

<template>
  <div class="space-y-5" v-loading="loading">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold text-slate-800">D8.4 business demo walkthrough</h2>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          A partner-facing operating story for intelliOffice PartnerOS: customer development to product adaptation,
          quote, order, partner split, production, shipment, Portal, feedback, and market response.
        </p>
      </div>
      <div class="flex gap-2">
        <el-button @click="open('/')">Dashboard</el-button>
        <el-button type="primary" @click="load">Refresh</el-button>
      </div>
    </div>

    <el-alert type="info" :closable="false" :title="safety" />
    <el-alert v-if="error" type="error" :closable="false" :title="error" />

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">Demo story</h3>
        <el-tag effect="plain">agent operating system</el-tag>
      </div>
      <div class="grid gap-3 lg:grid-cols-3">
        <div v-for="line in storyLine" :key="line" class="rounded border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
          {{ line }}
        </div>
      </div>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">Operating loop</h3>
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

    <div class="grid gap-5 xl:grid-cols-2">
      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h3 class="font-semibold text-slate-800">Multi-partner coverage</h3>
          <el-tag effect="plain">partner neutral</el-tag>
        </div>
        <div class="grid gap-3 md:grid-cols-2">
          <div class="rounded border border-slate-100 p-3">
            <div class="text-xs uppercase text-slate-500">HOSUN direction</div>
            <div class="mt-1 font-semibold text-slate-900">{{ hosunPartner?.partner_name || 'HOSUN lifting systems' }}</div>
            <p class="mt-2 text-sm text-slate-600">
              Desk frames, desk legs, lifting columns, and heavy-duty lifting systems are represented as operating
              signals, not hard-coded platform preference.
            </p>
          </div>
          <div class="rounded border border-slate-100 p-3">
            <div class="text-xs uppercase text-slate-500">Second partner direction</div>
            <div class="mt-1 font-semibold text-slate-900">{{ secondaryPartner?.partner_name || 'JOOBOO education furniture' }}</div>
            <p class="mt-2 text-sm text-slate-600">
              Education furniture and project furniture demonstrate that PartnerOS supports multiple external brand
              operating lines.
            </p>
          </div>
        </div>
        <el-table :data="partnerRows" class="mt-4 w-full" size="small">
          <el-table-column prop="partner_name" label="Partner" min-width="190" />
          <el-table-column prop="order_count" label="Orders" width="90" />
          <el-table-column prop="split_count" label="Splits" width="90" />
          <el-table-column prop="active_shipment_count" label="Shipments" width="110" />
          <el-table-column label="Risk" min-width="160">
            <template #default="{ row }">
              <span v-if="!row.risk_flags.length" class="text-slate-400">clear</span>
              <el-tag v-for="flag in row.risk_flags" v-else :key="flag" size="small" type="warning" effect="plain">
                {{ flag }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h3 class="font-semibold text-slate-800">Two demo scenarios</h3>
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
          <h3 class="font-semibold text-slate-800">Featured customer-visible order</h3>
          <el-button size="small" :disabled="!featuredOrder" @click="openOrder(featuredOrder?.id)">Open order</el-button>
        </div>
        <template v-if="featuredOrder">
          <div class="rounded border border-slate-100 bg-slate-50 p-3">
            <div class="text-lg font-semibold text-slate-900">{{ featuredOrder.order_number }}</div>
            <div class="mt-1 text-sm text-slate-600">{{ featuredOrder.company_name || 'Customer account' }}</div>
            <div class="mt-3 grid gap-2 md:grid-cols-2">
              <el-tag effect="plain">{{ featuredOrder.portal_tracking.label || featuredOrder.portal_tracking.stage || 'Portal stage' }}</el-tag>
              <el-tag :type="featuredOrder.portal_tracking.has_production_updates ? 'success' : 'info'" effect="plain">
                production {{ featuredOrder.portal_tracking.has_production_updates ? 'visible' : 'pending' }}
              </el-tag>
              <el-tag :type="featuredOrder.portal_tracking.has_active_shipment ? 'success' : 'warning'" effect="plain">
                shipments {{ featuredOrder.portal_tracking.active_shipment_count }}
              </el-tag>
              <el-tag :type="featuredOrder.portal_tracking.has_open_feedback ? 'warning' : 'info'" effect="plain">
                feedback {{ featuredOrder.portal_tracking.open_feedback_count }}
              </el-tag>
            </div>
            <p class="mt-3 text-sm text-slate-600">{{ featuredOrder.portal_tracking.next_action_label || 'Review next customer-visible update.' }}</p>
          </div>
        </template>
        <el-empty v-else description="No customer-visible order found" />
      </section>
    </div>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">Market response signal explanation</h3>
        <el-button size="small" @click="open('/market-intelligence')">Open Market Response</el-button>
      </div>
      <el-table :data="marketExplanationRows" class="w-full">
        <el-table-column label="Focus" min-width="190">
          <template #default="{ row }">{{ focusLabel(row.key) }}</template>
        </el-table-column>
        <el-table-column prop="signal_score" label="Score" width="90" />
        <el-table-column prop="primary_signal" label="Primary signal" width="160" />
        <el-table-column prop="review_label" label="Review" min-width="210" />
        <el-table-column prop="reason" label="Why it matters" min-width="360" />
        <el-table-column label="Action" width="110">
          <template #default="{ row }">
            <el-button size="small" @click="router.push({ name: 'market', query: row.route_query })">Review</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="rounded border border-slate-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between gap-3">
        <h3 class="font-semibold text-slate-800">Portal operations evidence for the walkthrough</h3>
        <el-button size="small" @click="open('/portal-integration')">Open Portal Operations</el-button>
      </div>
      <div class="grid gap-3 md:grid-cols-4">
        <div class="rounded border border-slate-100 p-3">
          <div class="text-xs uppercase text-slate-500">Recent orders</div>
          <div class="mt-1 text-2xl font-semibold">{{ portal?.recent_customer_visible_orders.total ?? 0 }}</div>
        </div>
        <div class="rounded border border-slate-100 p-3">
          <div class="text-xs uppercase text-slate-500">Shipment risks</div>
          <div class="mt-1 text-2xl font-semibold">
            {{ (portal?.shipment_readiness.missing_estimated_dates_count ?? 0) + (portal?.shipment_readiness.shipped_without_tracking_count ?? 0) }}
          </div>
        </div>
        <div class="rounded border border-slate-100 p-3">
          <div class="text-xs uppercase text-slate-500">Feedback open</div>
          <div class="mt-1 text-2xl font-semibold">{{ portal?.feedback_operations.open_count ?? 0 }}</div>
        </div>
        <div class="rounded border border-slate-100 p-3">
          <div class="text-xs uppercase text-slate-500">Market previews</div>
          <div class="mt-1 text-2xl font-semibold">{{ portal?.market_signal_preview.total ?? 0 }}</div>
        </div>
      </div>
    </section>
  </div>
</template>
