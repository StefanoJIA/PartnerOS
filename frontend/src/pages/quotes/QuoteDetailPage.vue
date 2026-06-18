<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createOrderFromQuote, fetchOrders, type OrderSummary } from '@/api/orders'
import {
  createQuoteLearning,
  exportQuotePdf,
  fetchDeliveryLogs,
  fetchOrderReadiness,
  fetchQuote,
  fetchQuoteLearning,
  fetchQuotePdfExports,
  fetchQuoteTimeline,
  fetchQuoteVersions,
  markQuoteReady,
  markQuoteSent,
  promoteQuoteLearningToMarketResponse,
  quotePdfDownloadUrl,
  SENT_CHANNELS,
  type DeliveryLog,
  type OrderReadiness,
  type PdfExportRecord,
  type QuoteDetail,
  type QuoteLearningRecord,
  type QuoteVersionSummary,
  type TimelineItem,
} from '@/api/quotes'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const successMsg = ref('')
const quote = ref<QuoteDetail | null>(null)
const actionLoading = ref(false)

const pdfExports = ref<PdfExportRecord[]>([])
const pdfLoading = ref(false)
const pdfError = ref('')
const pdfExporting = ref(false)

const deliveryLogs = ref<DeliveryLog[]>([])
const deliveryLoading = ref(false)
const deliveryError = ref('')
const deliverySubmitting = ref(false)
const showDeliveryForm = ref(false)

const timelineItems = ref<TimelineItem[]>([])
const timelineLoading = ref(false)
const versions = ref<QuoteVersionSummary[]>([])

const readiness = ref<OrderReadiness | null>(null)
const readinessLoading = ref(false)
const readinessError = ref('')
const copyMsg = ref('')
const activeOrder = ref<OrderSummary | null>(null)
const createOrderLoading = ref(false)
const showCreateOrderModal = ref(false)
const createWithConfirmation = ref(false)
const createOrderNote = ref('')

const learningRecords = ref<QuoteLearningRecord[]>([])
const learningLoading = ref(false)
const learningSaving = ref(false)
const learningPromotingId = ref('')
const learningError = ref('')

const deliveryForm = reactive({
  sent_channel: 'email',
  sent_to_name: '',
  sent_to_email: '',
  sent_to_company: '',
  pdf_export_id: '',
  quote_version_id: '',
  sent_at: '',
  follow_up_date: '',
  note: '',
})

const learningForm = reactive({
  outcome_status: 'customer_reviewing',
  customer_feedback: '',
  customer_objection: '',
  competitor_signal: '',
  reason_category: 'unknown',
  customer_decision_factors_text: 'price, delivery, certification',
  won_reason: '',
  lost_reason: '',
  price_feedback: '',
  delivery_feedback: '',
  product_dimensions_text: 'load, stability, noise, delivery, installation, warranty, certification, project demand',
  product_factors_text: 'load, stability, noise, packaging, warranty, certification',
  partner_factors_text: 'partner capacity, delivery support, certification support',
  next_action: '',
  owner: '',
  follow_up_date: '',
  affects_product_intelligence: true,
  affects_market_response: true,
  affects_opportunity: true,
  internal_only: true,
})

const SAFETY =
  '报价记录只保存内部报价和报价模型快照；系统不会自动发送邮件、通知客户、承诺库存、认证或交期。'
const PDF_SAFETY = '导出 PDF 只生成客户报价文件，不会自动发送，也不会自动承诺库存、认证或交期。'
const DELIVERY_SAFETY =
  '人工发送记录只用于留档；系统不会自动发送邮件、LinkedIn、附件或客户通知。'
const READINESS_SAFETY =
  '转订单检查只用于人工判断，不会自动创建订单、启动生产、创建物流或确认客户接受。'
const CREATE_ORDER_SAFETY =
  '从报价创建订单不会自动启动生产、通知供应商、创建物流、承诺库存、认证或交期。'
const LEARNING_SAFETY =
  '报价复盘只记录内部人工判断；不自动发送消息，不改变报价/订单状态，不写入客户 Portal。'

const outcomeOptions = [
  { value: 'won', label: '赢单' },
  { value: 'lost', label: '丢单' },
  { value: 'no_response', label: '无回应' },
  { value: 'deferred', label: '延期决策' },
  { value: 'still_active', label: '仍在推进' },
  { value: 'customer_reviewing', label: '客户评估中' },
  { value: 'revision_requested', label: '需要修订报价' },
]

const reasonCategoryOptions = [
  { value: 'price', label: '价格 / 价值解释' },
  { value: 'delivery', label: '交期 / 交付' },
  { value: 'certification', label: '认证 / 技术资料' },
  { value: 'product_fit', label: '产品匹配' },
  { value: 'partner_capacity', label: 'Partner 承接能力' },
  { value: 'customer_budget', label: '客户预算' },
  { value: 'competitor', label: '竞争因素' },
  { value: 'timing', label: '采购时机' },
  { value: 'relationship', label: '客户关系' },
  { value: 'unknown', label: '未知 / 待确认' },
]

const warnings = computed(() => quote.value?.warnings ?? [])
const quoteIntervalLines = computed(() =>
  (quote.value?.line_items ?? []).filter((line) => (line.interval_quote_table ?? []).length > 0),
)
const latestLearning = computed(() => quote.value?.latest_learning || learningRecords.value[0] || null)
const canMarkSent = computed(
  () => quote.value && (quote.value.status === 'ready_to_send' || quote.value.status === 'sent') && !quote.value.derived_expired,
)
const canCreateOrder = computed(
  () =>
    quote.value?.status === 'sent' &&
    !quote.value.derived_expired &&
    !activeOrder.value &&
    readiness.value &&
    readiness.value.blocking_items.length === 0,
)

function quoteStatusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: '草稿',
    internal_review: '内部审核',
    ready_to_send: '待人工发送',
    sent: '已人工发送',
    accepted: '客户接受',
    expired: '已过期',
    cancelled: '已取消',
  }
  return labels[status] || status
}

function readinessStatusLabel(status: string) {
  const labels: Record<string, string> = {
    ready_for_order_review: '可进入订单人工复核',
    needs_customer_confirmation: '需要客户确认',
    needs_internal_review: '需要内部复核',
    not_ready: '暂不可转订单',
  }
  return labels[status] || status
}

function statusTagType(status: string) {
  if (status === 'ready_for_order_review') return 'success'
  if (status === 'needs_customer_confirmation') return 'warning'
  if (status === 'needs_internal_review') return 'danger'
  return 'info'
}

function formatIntervalPrice(value: string | null | undefined, currency = 'USD') {
  return value ? `${currency} ${value}` : 'N/A'
}

function splitLabels(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

async function loadActiveOrder() {
  if (!quote.value) return
  try {
    const data = await fetchOrders({ quote_id: quote.value.id })
    activeOrder.value = data.items.find((o) => o.status !== 'cancelled') ?? null
  } catch {
    activeOrder.value = null
  }
}

async function loadPdfExports() {
  if (!quote.value) return
  pdfLoading.value = true
  pdfError.value = ''
  try {
    const data = await fetchQuotePdfExports(quote.value.id)
    pdfExports.value = data.items
    if (!deliveryForm.pdf_export_id && data.items.length) {
      deliveryForm.pdf_export_id = data.items[0].export_id
    }
  } catch (e: unknown) {
    pdfError.value = e instanceof Error ? e.message : 'PDF 记录加载失败'
  } finally {
    pdfLoading.value = false
  }
}

async function loadDeliveryLogs() {
  if (!quote.value) return
  deliveryLoading.value = true
  deliveryError.value = ''
  try {
    const data = await fetchDeliveryLogs(quote.value.id)
    deliveryLogs.value = data.items
  } catch (e: unknown) {
    deliveryError.value = e instanceof Error ? e.message : '人工发送记录加载失败'
  } finally {
    deliveryLoading.value = false
  }
}

async function loadLearning() {
  if (!quote.value) return
  learningLoading.value = true
  learningError.value = ''
  try {
    const data = await fetchQuoteLearning(quote.value.id)
    learningRecords.value = data.items
  } catch (e: unknown) {
    learningError.value = e instanceof Error ? e.message : '报价复盘记录加载失败'
  } finally {
    learningLoading.value = false
  }
}

async function loadTimeline() {
  if (!quote.value) return
  timelineLoading.value = true
  try {
    const data = await fetchQuoteTimeline(quote.value.id)
    timelineItems.value = data.items
  } catch {
    timelineItems.value = []
  } finally {
    timelineLoading.value = false
  }
}

async function loadVersions() {
  if (!quote.value) return
  try {
    const data = await fetchQuoteVersions(quote.value.id)
    versions.value = data.items
    if (!deliveryForm.quote_version_id && data.items.length) {
      deliveryForm.quote_version_id = data.items[data.items.length - 1].id
    }
  } catch {
    versions.value = []
  }
}

async function loadReadiness() {
  if (!quote.value) return
  readinessLoading.value = true
  readinessError.value = ''
  try {
    readiness.value = await fetchOrderReadiness(quote.value.id)
  } catch (e: unknown) {
    readinessError.value = e instanceof Error ? e.message : '转订单检查加载失败'
  } finally {
    readinessLoading.value = false
  }
}

function prefillDeliveryForm() {
  if (!quote.value) return
  deliveryForm.sent_to_name = deliveryForm.sent_to_name || quote.value.bill_to_company || ''
  deliveryForm.sent_to_company = deliveryForm.sent_to_company || quote.value.bill_to_company || ''
}

async function load() {
  loading.value = true
  error.value = ''
  successMsg.value = ''
  try {
    quote.value = await fetchQuote(String(route.params.id))
    prefillDeliveryForm()
    await Promise.all([
      loadPdfExports(),
      loadDeliveryLogs(),
      loadLearning(),
      loadTimeline(),
      loadVersions(),
      loadReadiness(),
      loadActiveOrder(),
    ])
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '报价详情加载失败'
  } finally {
    loading.value = false
  }
}

async function onExportPdf() {
  if (!quote.value) return
  pdfExporting.value = true
  pdfError.value = ''
  try {
    await exportQuotePdf(quote.value.id)
    await loadPdfExports()
    await loadTimeline()
    successMsg.value = '客户报价 PDF 已生成，可手动下载或人工发送。'
  } catch (e: unknown) {
    pdfError.value = e instanceof Error ? e.message : 'PDF 导出失败'
  } finally {
    pdfExporting.value = false
  }
}

async function onMarkReady() {
  if (!quote.value) return
  actionLoading.value = true
  error.value = ''
  try {
    quote.value = await markQuoteReady(quote.value.id)
    successMsg.value = '报价已标记为待人工发送。'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '状态更新失败'
  } finally {
    actionLoading.value = false
  }
}

async function onSubmitDelivery() {
  if (!quote.value) return
  deliverySubmitting.value = true
  deliveryError.value = ''
  successMsg.value = ''
  try {
    const result = await markQuoteSent(quote.value.id, {
      sent_channel: deliveryForm.sent_channel,
      sent_to_name: deliveryForm.sent_to_name || undefined,
      sent_to_email: deliveryForm.sent_to_email || undefined,
      sent_to_company: deliveryForm.sent_to_company || undefined,
      pdf_export_id: deliveryForm.pdf_export_id || undefined,
      quote_version_id: deliveryForm.quote_version_id || undefined,
      sent_at: deliveryForm.sent_at || undefined,
      follow_up_date: deliveryForm.follow_up_date || undefined,
      note: deliveryForm.note || undefined,
    })
    quote.value = await fetchQuote(quote.value.id)
    successMsg.value = result.warnings?.length
      ? `人工发送已记录。${result.warnings.join(' ')}`
      : '人工发送已记录，报价状态已更新为已发送。'
    showDeliveryForm.value = false
    await Promise.all([loadDeliveryLogs(), loadTimeline(), loadReadiness()])
  } catch (e: unknown) {
    deliveryError.value = e instanceof Error ? e.message : '人工发送记录保存失败'
  } finally {
    deliverySubmitting.value = false
  }
}

function learningPayload() {
  return {
    outcome_status: learningForm.outcome_status,
    customer_feedback: learningForm.customer_feedback || null,
    customer_objection: learningForm.customer_objection || null,
    competitor_signal: learningForm.competitor_signal || null,
    reason_category: learningForm.reason_category || 'unknown',
    customer_decision_factors: splitLabels(learningForm.customer_decision_factors_text),
    won_reason: learningForm.won_reason || null,
    lost_reason: learningForm.lost_reason || null,
    price_feedback: learningForm.price_feedback || null,
    delivery_feedback: learningForm.delivery_feedback || null,
    product_dimensions: splitLabels(learningForm.product_dimensions_text),
    product_factors: splitLabels(learningForm.product_factors_text),
    partner_factors: splitLabels(learningForm.partner_factors_text),
    outcome_source_type: 'quote',
    outcome_source_id: quote.value?.id || null,
    next_action: learningForm.next_action || null,
    owner: learningForm.owner || null,
    follow_up_date: learningForm.follow_up_date || null,
    affects_product_intelligence: learningForm.affects_product_intelligence,
    affects_market_response: learningForm.affects_market_response,
    affects_opportunity: learningForm.affects_opportunity,
    internal_only: learningForm.internal_only,
  }
}

function resetLearningForm() {
  learningForm.customer_feedback = ''
  learningForm.customer_objection = ''
  learningForm.competitor_signal = ''
  learningForm.reason_category = 'unknown'
  learningForm.customer_decision_factors_text = 'price, delivery, certification'
  learningForm.won_reason = ''
  learningForm.lost_reason = ''
  learningForm.price_feedback = ''
  learningForm.delivery_feedback = ''
  learningForm.product_factors_text = 'load, stability, noise, packaging, warranty, certification'
  learningForm.partner_factors_text = 'partner capacity, delivery support, certification support'
  learningForm.next_action = ''
}

async function onSaveLearning() {
  if (!quote.value || learningSaving.value) return
  learningSaving.value = true
  learningError.value = ''
  successMsg.value = ''
  try {
    await createQuoteLearning(quote.value.id, learningPayload())
    quote.value = await fetchQuote(quote.value.id)
    await Promise.all([loadLearning(), loadTimeline(), loadReadiness()])
    resetLearningForm()
    successMsg.value = '报价复盘已保存；报价状态和订单状态未自动改变。'
  } catch (e: unknown) {
    learningError.value = e instanceof Error ? e.message : '报价复盘保存失败'
  } finally {
    learningSaving.value = false
  }
}

async function onPromoteLearning(row: QuoteLearningRecord) {
  if (!quote.value || learningPromotingId.value) return
  learningPromotingId.value = row.id
  learningError.value = ''
  successMsg.value = ''
  try {
    const result = await promoteQuoteLearningToMarketResponse(quote.value.id, row.id)
    successMsg.value = result.created
      ? `已生成 Market Response 审查项：${result.review.partner_focus} / ${result.review.review_dimension}`
      : `Market Response 审查项已存在：${result.review.partner_focus} / ${result.review.review_dimension}`
  } catch (e: unknown) {
    learningError.value = e instanceof Error ? e.message : '生成 Market Response 审查项失败'
  } finally {
    learningPromotingId.value = ''
  }
}

async function copyOrderSummary() {
  if (!readiness.value) return
  await navigator.clipboard.writeText(JSON.stringify(readiness.value.order_input_contract, null, 2))
  copyMsg.value = '订单输入摘要已复制'
}

async function copyMissingItems() {
  if (!readiness.value) return
  const items = [...readiness.value.blocking_items, ...readiness.value.warning_items]
  await navigator.clipboard.writeText(items.join('\n'))
  copyMsg.value = '阻塞/提醒项已复制'
}

async function onCreateOrder() {
  if (!quote.value) return
  createOrderLoading.value = true
  readinessError.value = ''
  try {
    const payload: Parameters<typeof createOrderFromQuote>[0] = { quote_id: quote.value.id }
    if (createWithConfirmation.value) {
      payload.customer_confirmation = {
        type: 'email',
        note: createOrderNote.value || 'Customer confirmed by email.',
      }
    }
    const result = await createOrderFromQuote(payload)
    showCreateOrderModal.value = false
    router.push({ name: 'order-detail', params: { orderId: result.id } })
  } catch (e: unknown) {
    readinessError.value = e instanceof Error ? e.message : '创建订单失败'
  } finally {
    createOrderLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="quote-detail-page">
    <div class="page-head">
      <div>
        <el-button link class="back-link" @click="$router.push({ name: 'quotes' })">返回报价列表</el-button>
        <h1 v-if="quote">报价详情 {{ quote.quote_number }}</h1>
        <p>这里仅处理该报价本身：客户报价、区间价格、PDF、人工发送记录和转订单检查。</p>
      </div>
      <div v-if="quote" class="head-actions">
        <el-tag :type="quote.status === 'sent' ? 'success' : 'info'" size="large">{{ quoteStatusLabel(quote.status) }}</el-tag>
        <el-button v-if="quote.status === 'internal_review'" type="primary" :loading="actionLoading" @click="onMarkReady">
          标记为待人工发送
        </el-button>
      </div>
    </div>

    <el-alert type="warning" :closable="false" show-icon title="安全边界" :description="SAFETY" class="mb" />
    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />
    <el-alert v-if="successMsg" type="success" :title="successMsg" show-icon class="mb" />
    <el-alert v-for="(w, i) in warnings" :key="i" type="warning" :title="w" show-icon class="mb" />

    <div v-if="loading" v-loading="true" class="loading-block" />
    <template v-else-if="quote">
      <section class="section quote-summary">
        <div class="section-title">
          <h2>报价基本信息</h2>
          <span>内部操作为中文；客户报价文件保持英文。</span>
        </div>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="报价状态">{{ quoteStatusLabel(quote.status) }}</el-descriptions-item>
          <el-descriptions-item label="报价日期">{{ quote.quote_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="有效至">{{ quote.valid_until }}</el-descriptions-item>
          <el-descriptions-item label="客户公司">{{ quote.bill_to_company || '-' }}</el-descriptions-item>
          <el-descriptions-item label="跟进日期">{{ quote.follow_up_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="人工发送时间">{{ quote.sent_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="付款条款">{{ quote.payment_terms || '-' }}</el-descriptions-item>
          <el-descriptions-item label="贸易条款">{{ quote.shipping_terms || '-' }}</el-descriptions-item>
          <el-descriptions-item label="内部参考总额">{{ quote.currency }} {{ quote.grand_total }}</el-descriptions-item>
        </el-descriptions>
      </section>

      <section v-if="quoteIntervalLines.length" class="section">
        <div class="section-title">
          <h2>客户报价区间表</h2>
          <span>每个产品完整展示所有数量区间；下单后再按实际数量形成准确订单总价。</span>
        </div>
        <div v-for="line in quoteIntervalLines" :key="line.id" class="interval-product">
          <div class="interval-product__head">
            <div>
              <strong>{{ line.product_name }}</strong>
              <p>{{ line.pricing_source || 'pricing model' }}</p>
            </div>
            <el-tag effect="plain">参考数量 {{ line.quantity }}</el-tag>
          </div>
          <el-table :data="line.interval_quote_table ?? []" size="small" border>
            <el-table-column prop="quantity_label" label="Quantity" width="150" />
            <el-table-column label="FOB Unit Price">
              <template #default="{ row }">{{ formatIntervalPrice(row.fob_unit_price, row.currency) }}</template>
            </el-table-column>
            <el-table-column label="DDP Unit Price">
              <template #default="{ row }">{{ formatIntervalPrice(row.ddp_unit_price, row.currency) }}</template>
            </el-table-column>
            <el-table-column label="Terms">
              <template #default="{ row }">{{ (row.incoterms_available ?? []).join(' / ') || '-' }}</template>
            </el-table-column>
          </el-table>
        </div>
      </section>

      <section class="section">
        <div class="section-title">
          <h2>报价产品明细</h2>
          <span>用于内部核对产品、参考数量和当前报价快照；成本与利润不在客户侧展示。</span>
        </div>
        <el-table :data="quote.line_items" stripe>
          <el-table-column prop="line_number" label="#" width="56" />
          <el-table-column prop="product_name" label="产品" min-width="260" />
          <el-table-column prop="quantity" label="参考数量" width="110" />
          <el-table-column prop="final_unit_price" label="参考单价" width="130" />
          <el-table-column prop="total_price" label="参考小计" width="130" />
          <el-table-column prop="pricing_source" label="计价来源" width="160" />
        </el-table>
      </section>

      <section class="section two-column">
        <div class="panel">
          <div class="section-title compact">
            <h2>客户 PDF</h2>
            <span>生成后仍需人工下载或发送。</span>
          </div>
          <el-alert type="info" :closable="false" show-icon title="PDF 安全边界" :description="PDF_SAFETY" class="mb" />
          <el-alert v-if="pdfError" type="error" :title="pdfError" show-icon class="mb" />
          <el-button type="primary" :loading="pdfExporting" @click="onExportPdf">导出客户 PDF</el-button>
          <div v-if="pdfLoading" v-loading="true" class="small-loading" />
          <el-empty v-else-if="!pdfExports.length" description="暂无 PDF 导出记录" class="mt" />
          <el-table v-else :data="pdfExports" stripe class="mt">
            <el-table-column prop="file_name" label="文件" min-width="180" />
            <el-table-column prop="exported_at" label="导出时间" width="170" />
            <el-table-column label="下载" width="90">
              <template #default="{ row }">
                <el-link :href="quotePdfDownloadUrl(quote.id, row.export_id)" target="_blank" type="primary">下载</el-link>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="panel">
          <div class="section-title compact">
            <h2>人工发送记录</h2>
            <span>只记录人工动作，不自动触达客户。</span>
          </div>
          <el-alert type="info" :closable="false" show-icon title="发送安全边界" :description="DELIVERY_SAFETY" class="mb" />
          <el-alert v-if="deliveryError" type="error" :title="deliveryError" show-icon class="mb" />
          <el-button v-if="canMarkSent" type="success" @click="showDeliveryForm = !showDeliveryForm">
            记录人工发送
          </el-button>

          <el-form v-if="showDeliveryForm" label-width="110px" class="delivery-form mt">
            <el-form-item label="渠道">
              <el-select v-model="deliveryForm.sent_channel" style="width: 220px">
                <el-option v-for="c in SENT_CHANNELS" :key="c.value" :label="c.label" :value="c.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="收件人">
              <el-input v-model="deliveryForm.sent_to_name" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="deliveryForm.sent_to_email" />
            </el-form-item>
            <el-form-item label="公司">
              <el-input v-model="deliveryForm.sent_to_company" />
            </el-form-item>
            <el-form-item label="PDF 文件">
              <el-select v-model="deliveryForm.pdf_export_id" clearable style="width: 100%">
                <el-option v-for="p in pdfExports" :key="p.export_id" :label="p.file_name" :value="p.export_id" />
              </el-select>
            </el-form-item>
            <el-form-item label="报价版本">
              <el-select v-model="deliveryForm.quote_version_id" clearable style="width: 220px">
                <el-option
                  v-for="v in versions"
                  :key="v.id"
                  :label="v.version_label || `v${v.version_number}`"
                  :value="v.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="跟进日期">
              <el-date-picker v-model="deliveryForm.follow_up_date" type="date" value-format="YYYY-MM-DD" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="deliveryForm.note" type="textarea" rows="2" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="deliverySubmitting" @click="onSubmitDelivery">保存发送记录</el-button>
            </el-form-item>
          </el-form>

          <div v-if="deliveryLoading" v-loading="true" class="small-loading" />
          <el-empty v-else-if="!deliveryLogs.length" description="暂无人工发送记录" class="mt" />
          <el-table v-else :data="deliveryLogs" stripe class="mt">
            <el-table-column prop="sent_at" label="发送时间" width="165" />
            <el-table-column prop="sent_channel" label="渠道" width="105" />
            <el-table-column prop="sent_to_name" label="收件人" />
            <el-table-column prop="sent_to_company" label="公司" />
            <el-table-column prop="follow_up_date" label="跟进" width="110" />
          </el-table>
        </div>
      </section>

      <section class="section">
        <div class="section-title">
          <h2>转订单准备</h2>
          <span>只做人工检查；是否创建订单由操作员明确执行。</span>
        </div>
        <el-alert type="warning" :closable="false" show-icon title="转订单安全边界" :description="READINESS_SAFETY" class="mb" />
        <el-alert v-if="readinessError" type="error" :title="readinessError" show-icon class="mb" />
        <el-alert v-if="copyMsg" type="success" :title="copyMsg" show-icon class="mb" @close="copyMsg = ''" />
        <div class="actions mb">
          <el-button :loading="readinessLoading" @click="loadReadiness">刷新检查</el-button>
          <el-button v-if="readiness" @click="copyOrderSummary">复制订单输入摘要</el-button>
          <el-button v-if="readiness" @click="copyMissingItems">复制阻塞/提醒项</el-button>
          <el-button v-if="canCreateOrder" type="primary" @click="showCreateOrderModal = true">创建订单</el-button>
          <el-button
            v-else-if="activeOrder"
            type="primary"
            @click="router.push({ name: 'order-detail', params: { orderId: activeOrder.id } })"
          >
            查看订单 {{ activeOrder.order_number }}
          </el-button>
        </div>

        <div v-if="readinessLoading" v-loading="true" class="small-loading" />
        <template v-else-if="readiness">
          <div class="readiness-bar">
            <el-tag :type="statusTagType(readiness.readiness_status)" size="large">
              {{ readinessStatusLabel(readiness.readiness_status) }}
            </el-tag>
            <strong>评分 {{ readiness.readiness_score }}</strong>
            <span>{{ readiness.recommended_next_action }}</span>
          </div>
          <el-alert
            v-if="readiness.blocking_items.length"
            type="error"
            title="阻塞项"
            :description="readiness.blocking_items.join(', ')"
            show-icon
            class="mb"
          />
          <el-alert
            v-if="readiness.warning_items.length"
            type="warning"
            title="提醒项"
            :description="readiness.warning_items.slice(0, 8).join(', ')"
            show-icon
            class="mb"
          />
          <el-table :data="readiness.checklist" stripe max-height="300">
            <el-table-column prop="label" label="检查项" min-width="220" />
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column prop="details" label="说明" min-width="280" />
          </el-table>
        </template>
        <el-empty v-else description="暂无转订单检查数据" class="mt" />
      </section>

      <section class="section internal-section">
        <el-collapse>
          <el-collapse-item name="learning">
            <template #title>
              <span class="collapse-title">内部记录：客户反馈 / 赢输原因 / Market Response</span>
            </template>
            <el-alert type="info" :closable="false" show-icon title="内部记录安全边界" :description="LEARNING_SAFETY" class="mb" />
            <el-alert v-if="learningError" type="error" :title="learningError" show-icon class="mb" />

            <div v-if="latestLearning" class="learning-summary mb">
              <div class="learning-summary__head">
                <el-tag type="primary" effect="plain">{{ latestLearning.outcome_status }}</el-tag>
                <span>{{ latestLearning.owner || '未指定 owner' }}</span>
                <span>{{ latestLearning.follow_up_date || '未设置跟进日期' }}</span>
              </div>
              <p v-if="latestLearning.customer_feedback">客户反馈：{{ latestLearning.customer_feedback }}</p>
              <p v-if="latestLearning.customer_objection">客户异议：{{ latestLearning.customer_objection }}</p>
              <p v-if="latestLearning.reason_category">原因分类：{{ latestLearning.reason_category }}</p>
              <p v-if="latestLearning.won_reason">赢单原因：{{ latestLearning.won_reason }}</p>
              <p v-if="latestLearning.lost_reason">丢单原因：{{ latestLearning.lost_reason }}</p>
              <p v-if="latestLearning.next_action">下一步：{{ latestLearning.next_action }}</p>
              <div class="chip-row">
                <el-tag
                  v-for="factor in latestLearning.customer_decision_factors"
                  :key="`decision-${factor}`"
                  size="small"
                  type="success"
                  effect="plain"
                >
                  {{ factor }}
                </el-tag>
                <el-tag
                  v-for="factor in latestLearning.product_factors"
                  :key="`product-${factor}`"
                  size="small"
                  type="warning"
                  effect="plain"
                >
                  {{ factor }}
                </el-tag>
                <el-tag
                  v-for="factor in latestLearning.partner_factors"
                  :key="`partner-${factor}`"
                  size="small"
                  type="info"
                  effect="plain"
                >
                  {{ factor }}
                </el-tag>
              </div>
              <el-button
                class="mt"
                size="small"
                type="warning"
                plain
                :loading="learningPromotingId === latestLearning.id"
                @click="onPromoteLearning(latestLearning)"
              >
                生成 Market Response 审查项
              </el-button>
            </div>
            <el-empty v-else description="暂无报价复盘记录；客户回复、报价修订、赢单或丢单后再记录原因。" class="mt" />

            <el-form label-width="140px" class="learning-form mt">
              <el-form-item label="结果状态">
                <el-select v-model="learningForm.outcome_status" style="width: 260px">
                  <el-option v-for="option in outcomeOptions" :key="option.value" :label="option.label" :value="option.value" />
                </el-select>
              </el-form-item>
              <el-form-item label="原因分类">
                <el-select v-model="learningForm.reason_category" style="width: 260px">
                  <el-option v-for="option in reasonCategoryOptions" :key="option.value" :label="option.label" :value="option.value" />
                </el-select>
              </el-form-item>
              <el-form-item label="客户反馈">
                <el-input
                  v-model="learningForm.customer_feedback"
                  type="textarea"
                  :rows="2"
                  placeholder="记录客户原始反馈摘要；不要写成本、利润或供应商私密信息。"
                />
              </el-form-item>
              <el-form-item label="客户异议">
                <el-input
                  v-model="learningForm.customer_objection"
                  type="textarea"
                  :rows="2"
                  placeholder="例如价格解释、交期、认证、安装、质保、噪音、承重等问题。"
                />
              </el-form-item>
              <el-form-item label="竞争情况">
                <el-input
                  v-model="learningForm.competitor_signal"
                  type="textarea"
                  :rows="2"
                  placeholder="只记录人工确认过的竞争信号；未知则留空。"
                />
              </el-form-item>
              <el-form-item label="客户决策因素">
                <el-input v-model="learningForm.customer_decision_factors_text" placeholder="price, delivery, certification, timing, relationship..." />
              </el-form-item>
              <el-form-item label="赢单 / 丢单原因">
                <div class="grid-two">
                  <el-input v-model="learningForm.won_reason" type="textarea" :rows="2" placeholder="赢单原因" />
                  <el-input v-model="learningForm.lost_reason" type="textarea" :rows="2" placeholder="丢单原因" />
                </div>
              </el-form-item>
              <el-form-item label="价格 / 交付反馈">
                <div class="grid-two">
                  <el-input v-model="learningForm.price_feedback" type="textarea" :rows="2" placeholder="客户对价格、价值解释、报价结构的反馈" />
                  <el-input v-model="learningForm.delivery_feedback" type="textarea" :rows="2" placeholder="客户对交期、物流、安装、交付风险的反馈" />
                </div>
              </el-form-item>
              <el-form-item label="产品维度">
                <el-input v-model="learningForm.product_dimensions_text" placeholder="load, stability, noise, warranty, certification, delivery..." />
              </el-form-item>
              <el-form-item label="产品 / Partner 因素">
                <div class="grid-two">
                  <el-input v-model="learningForm.product_factors_text" placeholder="HOSUN: load, stability, packaging; JOOBOO: durability, classroom deployment..." />
                  <el-input v-model="learningForm.partner_factors_text" placeholder="partner capacity, delivery support, certification support, after-sales..." />
                </div>
              </el-form-item>
              <el-form-item label="下一步 / Owner">
                <div class="grid-two">
                  <el-input v-model="learningForm.next_action" placeholder="下一步人工动作" />
                  <el-input v-model="learningForm.owner" placeholder="owner" />
                </div>
              </el-form-item>
              <el-form-item label="跟进日期">
                <el-date-picker v-model="learningForm.follow_up_date" type="date" value-format="YYYY-MM-DD" />
              </el-form-item>
              <el-form-item label="影响范围">
                <el-checkbox v-model="learningForm.affects_opportunity">影响项目机会</el-checkbox>
                <el-checkbox v-model="learningForm.affects_product_intelligence">影响产品洞察</el-checkbox>
                <el-checkbox v-model="learningForm.affects_market_response">影响 Market Response</el-checkbox>
                <el-checkbox v-model="learningForm.internal_only">内部可见</el-checkbox>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="learningSaving" @click="onSaveLearning">保存报价复盘记录</el-button>
              </el-form-item>
            </el-form>

            <div v-if="learningLoading" v-loading="true" class="small-loading" />
            <el-table v-else-if="learningRecords.length" :data="learningRecords" stripe class="mt">
              <el-table-column prop="outcome_status" label="结果" width="130" />
              <el-table-column prop="reason_category" label="原因分类" width="140" />
              <el-table-column prop="customer_objection" label="异议 / 反馈" min-width="220" />
              <el-table-column prop="next_action" label="下一步" min-width="220" />
              <el-table-column prop="owner" label="Owner" width="130" />
              <el-table-column prop="follow_up_date" label="跟进" width="120" />
              <el-table-column label="市场响应" width="150">
                <template #default="{ row }">
                  <el-button size="small" link type="warning" :loading="learningPromotingId === row.id" @click="onPromoteLearning(row)">
                    生成审查项
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>

          <el-collapse-item name="timeline">
            <template #title>
              <span class="collapse-title">内部记录：报价时间线</span>
            </template>
            <div v-if="timelineLoading" v-loading="true" class="small-loading" />
            <el-empty v-else-if="!timelineItems.length" description="暂无时间线记录" />
            <el-timeline v-else>
              <el-timeline-item v-for="(item, idx) in timelineItems" :key="idx" :timestamp="item.timestamp || ''">
                <strong>{{ item.title }}</strong>
                <span v-if="item.channel"> / {{ item.channel }}</span>
              </el-timeline-item>
            </el-timeline>
          </el-collapse-item>
        </el-collapse>
      </section>

      <el-dialog v-model="showCreateOrderModal" title="从报价创建订单" width="540px">
        <el-alert type="warning" :closable="false" show-icon title="安全边界" :description="CREATE_ORDER_SAFETY" class="mb" />
        <el-checkbox v-model="createWithConfirmation">包含客户确认记录，订单状态进入 confirmed</el-checkbox>
        <p v-if="!createWithConfirmation" class="hint">未包含客户确认时，订单会保持 pending_customer_confirmation。</p>
        <el-input
          v-if="createWithConfirmation"
          v-model="createOrderNote"
          class="mt"
          type="textarea"
          placeholder="客户确认备注"
          :rows="2"
        />
        <template #footer>
          <el-button @click="showCreateOrderModal = false">取消</el-button>
          <el-button type="primary" :loading="createOrderLoading" @click="onCreateOrder">创建订单</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<style scoped>
.quote-detail-page {
  min-height: 100%;
  padding: 20px 28px 48px;
  background: #f5f7fb;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.page-head h1 {
  margin: 4px 0 6px;
  color: #0f172a;
  font-size: 28px;
}

.page-head p {
  margin: 0;
  color: #64748b;
}

.back-link {
  padding-left: 0;
}

.head-actions,
.actions,
.chip-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.mb {
  margin-bottom: 16px;
}

.mt {
  margin-top: 14px;
}

.loading-block {
  min-height: 180px;
}

.small-loading {
  min-height: 90px;
  margin-top: 14px;
}

.section {
  margin-bottom: 18px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
}

.section-title {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.section-title h2 {
  margin: 0;
  color: #0f172a;
  font-size: 18px;
}

.section-title span {
  color: #64748b;
  font-size: 13px;
  text-align: right;
}

.section-title.compact {
  align-items: flex-start;
}

.two-column {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.panel {
  min-width: 0;
}

.interval-product {
  margin-top: 12px;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  overflow: hidden;
  background: #fbfdff;
}

.interval-product__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 14px;
}

.interval-product__head strong {
  color: #0f172a;
}

.interval-product__head p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 13px;
}

.delivery-form,
.learning-form {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  background: #f8fafc;
}

.readiness-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.readiness-bar span {
  color: #475569;
}

.internal-section {
  background: #f8fafc;
}

.collapse-title {
  color: #0f172a;
  font-weight: 600;
}

.learning-summary {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}

.learning-summary__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  color: #64748b;
  font-size: 13px;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
}

.hint {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 13px;
}

@media (max-width: 980px) {
  .page-head,
  .section-title {
    flex-direction: column;
    align-items: flex-start;
  }

  .section-title span {
    text-align: left;
  }

  .two-column,
  .grid-two {
    grid-template-columns: 1fr;
  }
}
</style>
