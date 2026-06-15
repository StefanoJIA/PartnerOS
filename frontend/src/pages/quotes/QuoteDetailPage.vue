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
import AccountExecutionCard from '@/components/business/AccountExecutionCard.vue'

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

const learningForm = reactive({
  outcome_status: 'customer_reviewing',
  customer_feedback: '',
  customer_objection: '',
  competitor_signal: '',
  won_reason: '',
  lost_reason: '',
  price_feedback: '',
  delivery_feedback: '',
  product_dimensions_text: 'load, stability, noise, delivery, installation, warranty, certification, project demand',
  next_action: '',
  owner: '',
  follow_up_date: '',
  affects_product_intelligence: true,
  affects_market_response: true,
  affects_opportunity: true,
  internal_only: true,
})

const CREATE_ORDER_SAFETY =
  'Creating an order does not start production, notify suppliers, create shipments, or confirm inventory, certifications, or lead times.'

const READINESS_SAFETY =
  'This readiness check does not create an order, start production, create shipment, or confirm customer acceptance. Conversion to order must be a separate manual action in a future stage.'

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

const SAFETY =
  'Quote records are manually prepared. intelliOffice does not send quotes automatically, does not promise inventory, certifications, or lead times.'

const PDF_SAFETY =
  'Exporting a PDF does not send the quote, promise inventory, confirm certifications, or commit to lead times.'

const DELIVERY_SAFETY =
  'Recording a sent quote only documents a manual external action. intelliOffice does not send emails, LinkedIn messages, or attachments automatically.'

const LEARNING_SAFETY =
  '报价学习只记录人工复盘：不自动发送消息、不改变报价/订单状态、不把客户不可见信息写入 Portal。'

const outcomeOptions = [
  { value: 'open', label: '仍在推进' },
  { value: 'customer_reviewing', label: '客户评估中' },
  { value: 'revision_requested', label: '需要修订报价' },
  { value: 'won', label: '赢单信号' },
  { value: 'lost', label: '丢单信号' },
  { value: 'no_decision', label: '客户暂无决策' },
  { value: 'on_hold', label: '暂停等待' },
]

const warnings = computed(() => quote.value?.warnings ?? [])
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
const latestLearning = computed(() => quote.value?.latest_learning || learningRecords.value[0] || null)
const quoteCompanyId = computed(() => quote.value?.company_id ?? null)

async function loadActiveOrder() {
  if (!quote.value) return
  try {
    const data = await fetchOrders({ quote_id: quote.value.id })
    activeOrder.value = data.items.find((o) => o.status !== 'cancelled') ?? null
  } catch {
    activeOrder.value = null
  }
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
    readinessError.value = e instanceof Error ? e.message : 'Create order failed'
  } finally {
    createOrderLoading.value = false
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
    pdfError.value = e instanceof Error ? e.message : 'Failed to load PDF exports'
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
    deliveryError.value = e instanceof Error ? e.message : 'Failed to load delivery logs'
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
    learningError.value = e instanceof Error ? e.message : '报价学习记录加载失败'
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

async function loadReadiness() {
  if (!quote.value) return
  readinessLoading.value = true
  readinessError.value = ''
  try {
    readiness.value = await fetchOrderReadiness(quote.value.id)
  } catch (e: unknown) {
    readinessError.value = e instanceof Error ? e.message : 'Failed to load order readiness'
  } finally {
    readinessLoading.value = false
  }
}

function statusTagType(status: string) {
  if (status === 'needs_customer_confirmation') return 'warning'
  if (status === 'needs_internal_review') return 'danger'
  if (status === 'ready_for_order_review') return 'success'
  return 'info'
}

async function copyOrderSummary() {
  if (!readiness.value) return
  const text = JSON.stringify(readiness.value.order_input_contract, null, 2)
  await navigator.clipboard.writeText(text)
  copyMsg.value = 'Order input summary copied'
}

async function copyMissingItems() {
  if (!readiness.value) return
  const items = [...readiness.value.blocking_items, ...readiness.value.warning_items]
  await navigator.clipboard.writeText(items.join('\n'))
  copyMsg.value = 'Missing / warning items copied'
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
    await Promise.all([loadPdfExports(), loadDeliveryLogs(), loadLearning(), loadTimeline(), loadVersions(), loadReadiness(), loadActiveOrder()])
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load quote'
  } finally {
    loading.value = false
  }
}

function learningPayload() {
  const productDimensions = learningForm.product_dimensions_text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
  return {
    outcome_status: learningForm.outcome_status,
    customer_feedback: learningForm.customer_feedback || null,
    customer_objection: learningForm.customer_objection || null,
    competitor_signal: learningForm.competitor_signal || null,
    won_reason: learningForm.won_reason || null,
    lost_reason: learningForm.lost_reason || null,
    price_feedback: learningForm.price_feedback || null,
    delivery_feedback: learningForm.delivery_feedback || null,
    product_dimensions: productDimensions,
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
  learningForm.won_reason = ''
  learningForm.lost_reason = ''
  learningForm.price_feedback = ''
  learningForm.delivery_feedback = ''
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
    successMsg.value = '报价学习记录已保存；报价状态和订单状态未自动改变。'
  } catch (e: unknown) {
    learningError.value = e instanceof Error ? e.message : '保存报价学习记录失败'
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

async function onExportPdf() {
  if (!quote.value) return
  pdfExporting.value = true
  pdfError.value = ''
  try {
    await exportQuotePdf(quote.value.id)
    await loadPdfExports()
    await loadTimeline()
  } catch (e: unknown) {
    pdfError.value = e instanceof Error ? e.message : 'PDF export failed'
  } finally {
    pdfExporting.value = false
  }
}

async function onMarkReady() {
  if (!quote.value) return
  actionLoading.value = true
  try {
    quote.value = await markQuoteReady(quote.value.id)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Mark ready failed'
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
      ? `Delivery recorded. ${result.warnings.join(' ')}`
      : 'Delivery recorded — quote marked as sent.'
    showDeliveryForm.value = false
    await Promise.all([loadDeliveryLogs(), loadTimeline(), loadReadiness()])
  } catch (e: unknown) {
    deliveryError.value = e instanceof Error ? e.message : 'Mark sent failed'
  } finally {
    deliverySubmitting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <el-button link @click="$router.push({ name: 'quotes' })">← Back to Quotes</el-button>
    <h1 v-if="quote">{{ quote.quote_number }}</h1>
    <el-alert type="warning" :closable="false" show-icon title="Safety" :description="SAFETY" class="mb" />
    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />
    <el-alert v-if="successMsg" type="success" :title="successMsg" show-icon class="mb" />
    <el-alert v-for="(w, i) in warnings" :key="i" type="warning" :title="w" show-icon class="mb" />

    <div v-if="loading" v-loading="true" style="min-height: 160px" />
    <template v-else-if="quote">
      <el-descriptions :column="2" border class="mb">
        <el-descriptions-item label="Status">{{ quote.status }}</el-descriptions-item>
        <el-descriptions-item label="Valid Until">{{ quote.valid_until }}</el-descriptions-item>
        <el-descriptions-item label="Follow-up">{{ quote.follow_up_date || '—' }}</el-descriptions-item>
        <el-descriptions-item label="Sent At">{{ quote.sent_at || '—' }}</el-descriptions-item>
        <el-descriptions-item label="Payment Terms">{{ quote.payment_terms }}</el-descriptions-item>
        <el-descriptions-item label="Shipping Terms">{{ quote.shipping_terms }}</el-descriptions-item>
        <el-descriptions-item label="Subtotal">{{ quote.currency }} {{ quote.subtotal }}</el-descriptions-item>
        <el-descriptions-item label="Grand Total">{{ quote.currency }} {{ quote.grand_total }}</el-descriptions-item>
      </el-descriptions>

      <AccountExecutionCard
        :company-id="quoteCompanyId"
        context-label="当前报价会影响账户成交、报价学习和 Market Response"
      />

      <h3>Line Items</h3>
      <el-table :data="quote.line_items" stripe class="mb">
        <el-table-column prop="line_number" label="#" width="50" />
        <el-table-column prop="product_name" label="Product" />
        <el-table-column prop="quantity" label="Qty" width="80" />
        <el-table-column prop="final_unit_price" label="Unit Price" width="120" />
        <el-table-column prop="total_price" label="Total" width="120" />
        <el-table-column prop="pricing_source" label="Source" width="140" />
      </el-table>

      <section class="section mb">
        <h3>Quote PDF Exports</h3>
        <el-alert type="info" :closable="false" show-icon title="PDF Safety" :description="PDF_SAFETY" class="mb" />
        <el-alert v-if="pdfError" type="error" :title="pdfError" show-icon class="mb" />
        <el-button type="primary" :loading="pdfExporting" @click="onExportPdf">Export Customer PDF</el-button>
        <div v-if="pdfLoading" v-loading="true" style="min-height: 80px; margin-top: 16px" />
        <el-empty v-else-if="!pdfExports.length" description="No PDF exports yet" class="mt" />
        <el-table v-else :data="pdfExports" stripe class="mt">
          <el-table-column prop="file_name" label="File" />
          <el-table-column prop="exported_at" label="Exported At" width="200" />
          <el-table-column label="Download" width="120">
            <template #default="{ row }">
              <el-link :href="quotePdfDownloadUrl(quote.id, row.export_id)" target="_blank" type="primary">
                Download
              </el-link>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="section mb">
        <h3>Quote Delivery</h3>
        <el-alert type="info" :closable="false" show-icon title="Delivery Safety" :description="DELIVERY_SAFETY" class="mb" />
        <el-alert v-if="deliveryError" type="error" :title="deliveryError" show-icon class="mb" />
        <el-button
          v-if="canMarkSent"
          type="success"
          @click="showDeliveryForm = !showDeliveryForm"
        >
          Mark as Sent (manual)
        </el-button>

        <el-form v-if="showDeliveryForm" label-width="140px" class="delivery-form mt">
          <el-form-item label="Channel">
            <el-select v-model="deliveryForm.sent_channel" style="width: 240px">
              <el-option v-for="c in SENT_CHANNELS" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="Sent to name">
            <el-input v-model="deliveryForm.sent_to_name" />
          </el-form-item>
          <el-form-item label="Sent to email">
            <el-input v-model="deliveryForm.sent_to_email" />
          </el-form-item>
          <el-form-item label="Sent to company">
            <el-input v-model="deliveryForm.sent_to_company" />
          </el-form-item>
          <el-form-item label="PDF export">
            <el-select v-model="deliveryForm.pdf_export_id" clearable style="width: 100%">
              <el-option v-for="p in pdfExports" :key="p.export_id" :label="p.file_name" :value="p.export_id" />
            </el-select>
          </el-form-item>
          <el-form-item label="Version">
            <el-select v-model="deliveryForm.quote_version_id" clearable style="width: 240px">
              <el-option
                v-for="v in versions"
                :key="v.id"
                :label="v.version_label || `v${v.version_number}`"
                :value="v.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="Follow-up date">
            <el-date-picker v-model="deliveryForm.follow_up_date" type="date" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="Note">
            <el-input v-model="deliveryForm.note" type="textarea" rows="2" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="deliverySubmitting" @click="onSubmitDelivery">
              Record Manual Delivery
            </el-button>
          </el-form-item>
        </el-form>

        <div v-if="deliveryLoading" v-loading="true" style="min-height: 80px; margin-top: 16px" />
        <el-empty v-else-if="!deliveryLogs.length" description="No delivery logs yet" class="mt" />
        <el-table v-else :data="deliveryLogs" stripe class="mt">
          <el-table-column prop="sent_at" label="Sent At" width="180" />
          <el-table-column prop="sent_channel" label="Channel" width="120" />
          <el-table-column prop="sent_to_name" label="Recipient" />
          <el-table-column prop="sent_to_company" label="Company" />
          <el-table-column prop="follow_up_date" label="Follow-up" width="120" />
        </el-table>
      </section>

      <section class="section mb">
        <h3>报价学习 / 客户反馈</h3>
        <el-alert type="info" :closable="false" show-icon title="安全边界" :description="LEARNING_SAFETY" class="mb" />
        <el-alert v-if="learningError" type="error" :title="learningError" show-icon class="mb" />

        <div v-if="latestLearning" class="learning-summary mb">
          <div class="learning-summary__head">
            <el-tag type="primary" effect="plain">{{ latestLearning.outcome_status }}</el-tag>
            <span>{{ latestLearning.owner || '未指定 owner' }}</span>
            <span>{{ latestLearning.follow_up_date || '未设跟进日期' }}</span>
          </div>
          <p v-if="latestLearning.customer_feedback">客户反馈：{{ latestLearning.customer_feedback }}</p>
          <p v-if="latestLearning.customer_objection">客户异议：{{ latestLearning.customer_objection }}</p>
          <p v-if="latestLearning.won_reason">赢单原因：{{ latestLearning.won_reason }}</p>
          <p v-if="latestLearning.lost_reason">丢单原因：{{ latestLearning.lost_reason }}</p>
          <p v-if="latestLearning.next_action">下一步：{{ latestLearning.next_action }}</p>
          <div class="mt">
            <el-tag
              v-for="dimension in latestLearning.product_dimensions"
              :key="dimension"
              size="small"
              effect="plain"
              class="mr"
            >
              {{ dimension }}
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
        <el-empty v-else description="暂无报价学习记录；请在客户回复、报价修订、赢单或丢单后记录原因。" class="mt" />

        <el-form label-width="150px" class="learning-form mt">
          <el-form-item label="结果状态">
            <el-select v-model="learningForm.outcome_status" style="width: 260px">
              <el-option v-for="option in outcomeOptions" :key="option.value" :label="option.label" :value="option.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="客户反馈">
            <el-input v-model="learningForm.customer_feedback" type="textarea" :rows="2" placeholder="记录客户原始反馈摘要，不写成本/利润/供应商私密信息。" />
          </el-form-item>
          <el-form-item label="客户异议">
            <el-input v-model="learningForm.customer_objection" type="textarea" :rows="2" placeholder="例如价格解释、交期、认证、安装、质保、噪音、承重等问题。" />
          </el-form-item>
          <el-form-item label="竞争情况">
            <el-input v-model="learningForm.competitor_signal" type="textarea" :rows="2" placeholder="只记录人工确认过的竞争信号；未知则留空。" />
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
            <el-button type="primary" :loading="learningSaving" @click="onSaveLearning">保存报价学习记录</el-button>
          </el-form-item>
        </el-form>

        <div v-if="learningLoading" v-loading="true" style="min-height: 80px" />
        <el-table v-else-if="learningRecords.length" :data="learningRecords" stripe class="mt">
          <el-table-column prop="outcome_status" label="结果" width="130" />
          <el-table-column prop="customer_objection" label="异议 / 反馈" />
          <el-table-column prop="next_action" label="下一步" />
          <el-table-column prop="owner" label="Owner" width="140" />
          <el-table-column prop="follow_up_date" label="跟进" width="120" />
          <el-table-column label="市场响应" width="160">
            <template #default="{ row }">
              <el-button
                size="small"
                link
                type="warning"
                :loading="learningPromotingId === row.id"
                @click="onPromoteLearning(row)"
              >
                生成审查项
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="section mb">
        <h3>Order Readiness</h3>
        <el-alert type="warning" :closable="false" show-icon title="Readiness Safety" :description="READINESS_SAFETY" class="mb" />
        <el-alert v-if="readinessError" type="error" :title="readinessError" show-icon class="mb" />
        <el-alert v-if="copyMsg" type="success" :title="copyMsg" show-icon class="mb" @close="copyMsg = ''" />
        <el-button :loading="readinessLoading" @click="loadReadiness">Refresh Readiness</el-button>
        <el-button v-if="readiness" @click="copyOrderSummary">Copy Order Input Summary</el-button>
        <el-button v-if="readiness" @click="copyMissingItems">Copy Missing Items</el-button>
        <el-button v-if="canCreateOrder" type="primary" @click="showCreateOrderModal = true">Create Order</el-button>
        <el-button
          v-else-if="activeOrder"
          type="primary"
          @click="router.push({ name: 'order-detail', params: { orderId: activeOrder.id } })"
        >
          View Order ({{ activeOrder.order_number }})
        </el-button>

        <el-dialog v-model="showCreateOrderModal" title="Create Order from Quote" width="520px">
          <el-alert type="warning" :closable="false" show-icon title="Safety" :description="CREATE_ORDER_SAFETY" class="mb" />
          <el-checkbox v-model="createWithConfirmation">Include customer confirmation (status → confirmed)</el-checkbox>
          <p v-if="!createWithConfirmation" class="hint">Without confirmation, order status will be pending_customer_confirmation.</p>
          <el-input
            v-if="createWithConfirmation"
            v-model="createOrderNote"
            class="mt"
            type="textarea"
            placeholder="Confirmation note"
            :rows="2"
          />
          <template #footer>
            <el-button @click="showCreateOrderModal = false">Cancel</el-button>
            <el-button type="primary" :loading="createOrderLoading" @click="onCreateOrder">Create Order</el-button>
          </template>
        </el-dialog>

        <div v-if="readinessLoading" v-loading="true" style="min-height: 100px; margin-top: 16px" />
        <template v-else-if="readiness">
          <div class="readiness-header mt">
            <el-tag :type="statusTagType(readiness.readiness_status)" size="large">
              {{ readiness.readiness_status }}
            </el-tag>
            <span class="score">Score: {{ readiness.readiness_score }}</span>
          </div>
          <p class="next-action">{{ readiness.recommended_next_action }}</p>

          <el-alert
            v-if="readiness.blocking_items.length"
            type="error"
            title="Blocking items"
            :description="readiness.blocking_items.join(', ')"
            show-icon
            class="mb"
          />
          <el-alert
            v-if="readiness.warning_items.length"
            type="warning"
            title="Warnings"
            :description="readiness.warning_items.slice(0, 8).join(', ')"
            show-icon
            class="mb"
          />

          <el-table :data="readiness.checklist" stripe class="mt" max-height="320">
            <el-table-column prop="label" label="Check" />
            <el-table-column prop="status" label="Status" width="100" />
            <el-table-column prop="details" label="Details" />
          </el-table>

          <h4 class="mt">Order Input Contract Summary</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="Customer">
              {{ (readiness.order_input_contract.customer as Record<string, string>)?.company_name || '—' }}
            </el-descriptions-item>
            <el-descriptions-item label="Grand Total">
              {{ (readiness.order_input_contract.totals as Record<string, string>)?.currency }}
              {{ (readiness.order_input_contract.totals as Record<string, string>)?.grand_total }}
            </el-descriptions-item>
            <el-descriptions-item label="Line Items">
              {{ (readiness.order_input_contract.line_items as unknown[])?.length ?? 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="Source Quote">
              {{ (readiness.order_input_contract.source_quote as Record<string, string>)?.quote_number }}
            </el-descriptions-item>
          </el-descriptions>
        </template>
        <el-empty v-else description="No readiness data" class="mt" />
      </section>

      <section class="section mb">
        <h3>Quote Timeline</h3>
        <div v-if="timelineLoading" v-loading="true" style="min-height: 80px" />
        <el-empty v-else-if="!timelineItems.length" description="No timeline events yet" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="(item, idx) in timelineItems"
            :key="idx"
            :timestamp="item.timestamp || ''"
          >
            <strong>{{ item.title }}</strong>
            <span v-if="item.channel"> — {{ item.channel }}</span>
          </el-timeline-item>
        </el-timeline>
      </section>

      <div class="actions">
        <el-button
          v-if="quote.status === 'internal_review'"
          type="primary"
          :loading="actionLoading"
          @click="onMarkReady"
        >
          Mark Ready to Send
        </el-button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page { padding: 16px; }
.mb { margin-bottom: 16px; }
.mt { margin-top: 16px; }
.actions { display: flex; gap: 12px; }
.section { border-top: 1px solid var(--el-border-color); padding-top: 16px; }
.delivery-form { max-width: 640px; background: var(--el-fill-color-light); padding: 16px; border-radius: 8px; }
.readiness-header { display: flex; align-items: center; gap: 16px; }
.hint { font-size: 13px; color: #666; margin-top: 8px; }
.mt { margin-top: 12px; }
.mr { margin-right: 6px; }
.score { font-weight: 600; }
.next-action { margin: 12px 0; color: var(--el-text-color-secondary); }
.learning-summary { border: 1px solid var(--el-border-color); border-radius: 8px; background: var(--el-fill-color-light); padding: 12px; }
.learning-summary__head { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 8px; color: var(--el-text-color-secondary); font-size: 13px; }
.learning-form { max-width: 960px; background: var(--el-fill-color-lighter); padding: 16px; border-radius: 8px; }
.grid-two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; width: 100%; }
@media (max-width: 760px) {
  .grid-two { grid-template-columns: 1fr; }
}
</style>
