<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  fetchCatalogProducts,
  postPricingPreview,
  type CatalogProduct,
  type IntervalQuoteRow,
} from '@/api/quoteCatalog'
import { http } from '@/api/http'
import {
  exportQuotePdf,
  fetchQuoteCustomerOptions,
  fetchQuoteDraftSeed,
  createQuoteFromContract,
  type QuoteCustomerCompanyOption,
  type QuoteCustomerContactOption,
} from '@/api/quotes'
import { fetchQuoteInputContract, type QuoteInputContract } from '@/api/quoteInputContract'

type EditableIntervalRow = {
  min_qty: number
  max_qty: number | null
  quantity_label: string
  currency: string
  fob_unit_price: string
  ddp_unit_price: string
}

type QuoteProductBlock = {
  local_id: string
  product_id: string
  quantity: number
  incoterm: 'FOB' | 'DDP'
  pricing_strategy: string
  product: CatalogProduct
  rows: EditableIntervalRow[]
  loading: boolean
  source: string
  warnings: string[]
  cost_model: Record<string, string>
  interval_overridden: boolean
}

const DEFAULT_INTERVAL_ROWS: EditableIntervalRow[] = [
  { min_qty: 1, max_qty: 49, quantity_label: '1-49', currency: 'USD', fob_unit_price: '', ddp_unit_price: '' },
  { min_qty: 50, max_qty: 99, quantity_label: '50-99', currency: 'USD', fob_unit_price: '', ddp_unit_price: '' },
  { min_qty: 100, max_qty: 299, quantity_label: '100-299', currency: 'USD', fob_unit_price: '', ddp_unit_price: '' },
  { min_qty: 300, max_qty: 499, quantity_label: '300-499', currency: 'USD', fob_unit_price: '', ddp_unit_price: '' },
  { min_qty: 500, max_qty: null, quantity_label: '>=500', currency: 'USD', fob_unit_price: '', ddp_unit_price: '' },
]

const DEFAULT_PAYMENT_TERMS = [
  '30% deposit upon order placement;',
  '50% payment within one (1) calendar day after the goods depart the port of loading (ETD), against a copy of the "On Board" Bill of Lading or the carrier’s departure notice;',
  'The remaining 20% to be paid within two (2) weeks after receipt of the goods.',
].join('\n')
const DEFAULT_SHIPPING_INFORMATION = [
  'EXW (Ex Works): Price at the seller’s facility (Chongqing, China); the buyer is responsible for pickup, loading, export clearance, main carriage, insurance, and all costs/risks from collection.',
  'FOB (Free on Board): Price excludes shipping and insurance.',
  'CIF (Cost, Insurance, and Freight) to Boston: Price includes ocean freight and insurance up to the destination port (Boston).',
  'DDP (Delivered Duty Paid): Goods delivered to the final destination, with import duties and taxes included.',
].join('\n')
const DEFAULT_ADDITIONAL_NOTES = [
  'Description: Please provide a detailed description of the product or service.',
  'Quantity: Specify the required quantity of a single product model.',
  'Unit Price: Indicate the base price for each item.',
  'Discount: Apply any applicable discounts by amount or percentage.',
  'Tax Rate: Specify the applicable tax rate.',
  'Total: The final amount will be automatically calculated.',
].join('\n')

const router = useRouter()
const route = useRoute()
const leadId = computed(() => String(route.query.leadId || '').trim() || null)
const leadContract = ref<QuoteInputContract | null>(null)
const products = ref<CatalogProduct[]>([])
const selectedProductId = ref('')
const DEFAULT_MODEL_QUANTITY = 50
const DEFAULT_MODEL_INCOTERM: 'FOB' | 'DDP' = 'DDP'
const DEFAULT_MODEL_STRATEGY = 'volume'
const blocks = ref<QuoteProductBlock[]>([])
const loadingProducts = ref(false)
const creating = ref(false)
const error = ref('')
const quoteNumber = ref('')
const customerCompanies = ref<QuoteCustomerCompanyOption[]>([])
const customerContacts = ref<QuoteCustomerContactOption[]>([])
const selectedBillCompanyId = ref<string | null>(null)
const selectedBillContactId = ref<string | null>(null)
const selectedShipCompanyId = ref<string | null>(null)
const selectedShipContactId = ref<string | null>(null)

const quoteDate = ref(new Date().toISOString().slice(0, 10))
const validDays = ref(21)
const billTo = ref({ name: '', company: '', address: '' })
const shipTo = ref({ name: '', company: '', address: '' })
const thankYouText = ref('Thank you for your business!')
const paymentTermsText = ref(DEFAULT_PAYMENT_TERMS)
const manufacturingLeadTime = ref('21 to 28 days after order confirmed')
const ddpDeliveryTime = ref('45 to 50 days after order confirmed')
const shippingInformationText = ref(DEFAULT_SHIPPING_INFORMATION)
const additionalNotesText = ref(DEFAULT_ADDITIONAL_NOTES)

const selectedProduct = computed(() => products.value.find((item) => item.id === selectedProductId.value) ?? null)
const canCreate = computed(() => blocks.value.length > 0 && !creating.value)
const addedProductIds = computed(() => new Set(blocks.value.map((item) => item.product_id)))
const selectedProductAlreadyAdded = computed(() =>
  Boolean(selectedProductId.value && addedProductIds.value.has(selectedProductId.value)),
)
const validTill = computed(() => {
  const date = new Date(`${quoteDate.value}T00:00:00`)
  date.setDate(date.getDate() + validDays.value)
  return date.toLocaleDateString('en-US')
})
const paymentLines = computed(() => splitLines(paymentTermsText.value))
const shippingLines = computed(() => splitLines(shippingInformationText.value))
const additionalLines = computed(() => splitLines(additionalNotesText.value))
const billContactOptions = computed(() =>
  customerContacts.value.filter((item) => !selectedBillCompanyId.value || item.company_id === selectedBillCompanyId.value),
)
const shipContactOptions = computed(() =>
  customerContacts.value.filter((item) => !selectedShipCompanyId.value || item.company_id === selectedShipCompanyId.value),
)
const customerQuoteTerms = computed(() =>
  [
    thankYouText.value,
    '',
    'Terms & Instructions',
    'Payment Terms:',
    paymentTermsText.value,
    '',
    'Manufacturing Lead Time',
    manufacturingLeadTime.value,
    '',
    'DDP Delivery Time:',
    ddpDeliveryTime.value,
    '',
    'Shipping Information:',
    shippingInformationText.value,
    '',
    'Additional Notes:',
    additionalNotesText.value,
  ].join('\n'),
)

function splitLines(value: string) {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
}

function blankRows() {
  return DEFAULT_INTERVAL_ROWS.map((row) => ({ ...row }))
}

function normalizeRows(rows: IntervalQuoteRow[]): EditableIntervalRow[] {
  return rows.map((row) => ({
    min_qty: row.min_qty,
    max_qty: row.max_qty,
    quantity_label: row.quantity_label,
    currency: row.currency || 'USD',
    fob_unit_price: row.fob_unit_price || '',
    ddp_unit_price: row.ddp_unit_price || '',
  }))
}

function quotePayloadRows(block: QuoteProductBlock) {
  if (!block.interval_overridden && block.source !== 'manual_interval_blank') return null
  return block.rows.map((row) => ({
    min_qty: row.min_qty,
    max_qty: row.max_qty,
    quantity_label: row.quantity_label,
    currency: row.currency || 'USD',
    fob_unit_price: row.fob_unit_price || null,
    ddp_unit_price: row.ddp_unit_price || null,
  }))
}

function hasPrice(row: EditableIntervalRow) {
  return Boolean(String(row.fob_unit_price || '').trim() || String(row.ddp_unit_price || '').trim())
}

function productImage(product: CatalogProduct) {
  return product.image_url || ''
}

function productDisplayName(product: CatalogProduct) {
  const attrs = product.attributes_json || {}
  return String(attrs.customer_quote_name || product.product_name)
}

function productOptionLabel(product: CatalogProduct) {
  const suffix = addedProductIds.value.has(product.id) ? '（已添加）' : ''
  return `${product.internal_sku} - ${productDisplayName(product)}${suffix}`
}

function formatQuantityLabel(label: string) {
  return label.replace('>=', '≥').replace('-', ' ~ ')
}

function companyAddress(company: QuoteCustomerCompanyOption) {
  return company.address || [company.city, company.state, company.country].filter(Boolean).join(', ')
}

function findCompany(id: string | null) {
  return customerCompanies.value.find((item) => item.id === id) || null
}

function findContact(id: string | null) {
  return customerContacts.value.find((item) => item.id === id) || null
}

function applyCompany(target: 'bill' | 'ship') {
  const company = findCompany(target === 'bill' ? selectedBillCompanyId.value : selectedShipCompanyId.value)
  if (!company) return
  const address = target === 'bill' ? billTo.value : shipTo.value
  address.company = company.company_name
  address.address = companyAddress(company)
  if (target === 'bill') selectedBillContactId.value = null
  if (target === 'ship') selectedShipContactId.value = null
}

function applyContact(target: 'bill' | 'ship') {
  const contact = findContact(target === 'bill' ? selectedBillContactId.value : selectedShipContactId.value)
  if (!contact) return
  const address = target === 'bill' ? billTo.value : shipTo.value
  address.name = contact.full_name
  address.company = contact.company_name
  address.address = contact.company_address || address.address
  if (target === 'bill') selectedBillCompanyId.value = contact.company_id
  if (target === 'ship') selectedShipCompanyId.value = contact.company_id
}

async function loadQuoteSeed() {
  const seed = await fetchQuoteDraftSeed()
  quoteNumber.value = seed.quote_number
  validDays.value = seed.valid_days || validDays.value
}

async function loadCustomerOptions() {
  const data = await fetchQuoteCustomerOptions()
  customerCompanies.value = data.companies
  customerContacts.value = data.contacts
}

function warningText(block: QuoteProductBlock) {
  if (block.source === 'manual_interval_blank') return '需要手工补全该产品的区间价格。'
  if (block.warnings.length) return block.warnings.join(' / ')
  return '已加载底层成本和区间报价模型；成本、利润、物流测算保持内部可见。'
}

async function loadProducts() {
  loadingProducts.value = true
  error.value = ''
  try {
    const data = await fetchCatalogProducts({ limit: 200 })
    products.value = data.items
    if (data.items.length && !selectedProductId.value) selectedProductId.value = data.items[0].id
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '产品目录加载失败，请确认 backend 已启动。'
  } finally {
    loadingProducts.value = false
  }
}

async function addProductBlock() {
  const product = selectedProduct.value
  if (!product) {
    error.value = '请先选择要加入报价单的产品。'
    return
  }
  if (addedProductIds.value.has(product.id)) {
    error.value = '该产品已经在当前报价单中，请直接编辑下方区间价格；如需重新选择，请先删除该产品。'
    return
  }

  error.value = ''
  const localId = `${product.id}-${Date.now()}`
  blocks.value.push({
    local_id: localId,
    product_id: product.id,
    quantity: DEFAULT_MODEL_QUANTITY,
    incoterm: DEFAULT_MODEL_INCOTERM,
    pricing_strategy: DEFAULT_MODEL_STRATEGY,
    product,
    rows: [],
    loading: true,
    source: '',
    warnings: [],
    cost_model: {},
    interval_overridden: false,
  })

  try {
    const preview = await postPricingPreview({
      product_id: product.id,
      quantity: DEFAULT_MODEL_QUANTITY,
      incoterm: DEFAULT_MODEL_INCOTERM,
      pricing_strategy: DEFAULT_MODEL_STRATEGY,
    })
    const stage = preview.quote_model?.final_quote_stage as { interval_quote_table?: IntervalQuoteRow[] } | undefined
    const target = blocks.value.find((item) => item.local_id === localId)
    if (!target) return
    target.rows = normalizeRows(stage?.interval_quote_table || [])
    target.source = preview.source
    target.warnings = preview.warnings || []
    target.cost_model = preview.cost_breakdown || {}
    if (!target.rows.length) {
      target.rows = blankRows()
      target.source = 'manual_interval_blank'
      target.warnings = ['No interval price found; manual customer-visible prices required.']
      error.value = '该产品没有可用区间报价，已加入空白区间表，请手工填写客户可见单价后再保存。'
    }
  } catch (e: unknown) {
    const target = blocks.value.find((item) => item.local_id === localId)
    if (target) {
      target.rows = blankRows()
      target.source = 'manual_interval_blank'
      target.warnings = [e instanceof Error ? e.message : 'Preview failed; manual interval prices required.']
      error.value = '区间报价加载失败，已加入空白区间表，请手工填写客户可见单价后再保存。'
    }
  } finally {
    const target = blocks.value.find((item) => item.local_id === localId)
    if (target) target.loading = false
  }
}

function removeBlock(localId: string) {
  blocks.value = blocks.value.filter((item) => item.local_id !== localId)
}

function duplicateShipTo() {
  shipTo.value = { ...billTo.value }
  selectedShipCompanyId.value = selectedBillCompanyId.value
  selectedShipContactId.value = selectedBillContactId.value
}

async function loadLeadContext() {
  if (!leadId.value) {
    leadContract.value = null
    return
  }
  try {
    leadContract.value = await fetchQuoteInputContract(leadId.value)
    const customer = leadContract.value.quote_input_fields?.customer
    if (customer?.company_name) {
      billTo.value.company = customer.company_name
      if (customer.contact_name) billTo.value.name = customer.contact_name
      const matchedCompany = customerCompanies.value.find(
        (item) => item.company_name.toLowerCase() === customer.company_name.toLowerCase(),
      )
      if (matchedCompany) {
        selectedBillCompanyId.value = matchedCompany.id
        billTo.value.address = companyAddress(matchedCompany)
      }
      if (customer.contact_name) {
        const matchedContact = customerContacts.value.find(
          (item) => item.full_name.toLowerCase() === customer.contact_name?.toLowerCase(),
        )
        if (matchedContact) {
          selectedBillContactId.value = matchedContact.id
          selectedBillCompanyId.value = matchedContact.company_id
        }
      }
    }
  } catch {
    leadContract.value = null
  }
}

async function createQuote() {
  if (!blocks.value.length) {
    error.value = '请至少添加一个产品。'
    return
  }
  const incomplete = blocks.value.find((block) => block.rows.some((row) => !hasPrice(row)))
  if (incomplete) {
    error.value = `产品 ${incomplete.product.internal_sku} 存在未填写单价的数量区间；每个区间至少需要 FOB 或 DDP 价格。`
    return
  }

  creating.value = true
  error.value = ''
  try {
    const lineItems = blocks.value.map((block) => ({
      product_id: block.product_id,
      quantity: block.quantity,
      incoterm: block.incoterm,
      pricing_strategy: block.pricing_strategy,
      manual_interval_quote_table: quotePayloadRows(block),
    }))
    const sharedPayload = {
      line_items: lineItems,
      bill_to: billTo.value,
      ship_to: shipTo.value,
      payment_terms: paymentTermsText.value,
      shipping_terms: [
        `Manufacturing Lead Time: ${manufacturingLeadTime.value}`,
        `DDP Delivery Time: ${ddpDeliveryTime.value}`,
        shippingInformationText.value,
      ].join('\n'),
      internal_notes: leadId.value
        ? `Created from lead ${leadId.value} via quote input contract handoff.`
        : 'Created from editable quote sheet. Manual interval price overrides require internal review before sending.',
    }
    let quoteId: string | undefined
    if (leadId.value) {
      const created = await createQuoteFromContract({ lead_id: leadId.value, ...sharedPayload })
      quoteId = created.id
    } else {
      const { data } = await http.post('/v1/quotes', {
        quote_number: quoteNumber.value || null,
        company_id: selectedBillCompanyId.value,
        contact_id: selectedBillContactId.value,
        create_customer_if_missing: !selectedBillCompanyId.value && Boolean(billTo.value.company.trim()),
        ...sharedPayload,
        customer_notes: customerQuoteTerms.value,
      })
      if (data.ok && data.data?.id) quoteId = data.data.id
    }
    if (quoteId) {
      try {
        await exportQuotePdf(quoteId)
        ElMessage.success('报价已保存并生成客户 PDF；不会自动发送。')
      } catch (pdfError) {
        ElMessage.warning('报价已保存，但 PDF 生成失败；可在报价详情页手动导出。')
      }
      router.push({ name: 'quote-detail', params: { id: quoteId } })
    } else {
      error.value = '报价已提交但没有返回报价 ID，请刷新报价列表确认。'
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '创建报价失败。'
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  try {
    await Promise.all([loadProducts(), loadQuoteSeed(), loadCustomerOptions()])
    await loadLeadContext()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '报价初始化失败，请确认 backend 已启动。'
  }
})
</script>

<template>
  <div class="quote-editor-page">
    <div class="topbar">
      <div>
        <el-button link @click="router.push({ name: 'quotes' })">返回报价列表</el-button>
        <h1>新建报价单</h1>
        <p>操作系统为中文；客户报价正文保持英文。保存只创建内部报价记录，不会自动发送。</p>
      </div>
      <div class="topbar-actions">
        <el-button type="primary" :loading="creating" :disabled="!canCreate" @click="createQuote">保存报价</el-button>
      </div>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="安全边界"
      description="报价只会保存内部记录和报价模型快照；不会自动发送邮件、通知客户、承诺库存、认证或交期。成本、利润和物流测算保持内部可见。"
      class="notice"
    />
    <el-alert v-if="error" type="error" :title="error" show-icon class="notice" />
    <el-alert
      v-if="leadContract"
      type="success"
      :closable="false"
      show-icon
      class="notice"
      title="已关联线索报价输入合约"
      :description="`来自 ${leadContract.company_name} · 推荐产品范围：${leadContract.recommended_product_scope.join('、') || '待确认'}。保存时将写入合约快照，不会自动发送。`"
    />

    <section class="quote-shell">
      <div class="quote-paper">
        <header class="paper-header">
          <div class="brand-lockup">
            <img src="/intelliopus-logo.png" alt="IntelliOpus logo" />
          </div>
          <div class="brand-block">
            <h2>IntelliOpus Engineering</h2>
            <p>529 Main Street, Suite 2000, Charlestown, MA, 02129</p>
            <a href="https://www.intelli-opus.com" target="_blank" rel="noreferrer">www.intelli-opus.com</a>
            <p>(928) 679-3822</p>
          </div>
          <div class="header-quote-card">
            <span>QUOTE</span>
            <strong># {{ quoteNumber || '...' }}</strong>
          </div>
        </header>

        <section class="customer-block">
          <div class="address-grid">
            <div class="address-panel">
              <h3>BILL TO</h3>
              <el-select
                v-model="selectedBillCompanyId"
                clearable
                filterable
                placeholder="选择已有客户公司"
                class="document-input"
                @change="applyCompany('bill')"
              >
                <el-option
                  v-for="company in customerCompanies"
                  :key="company.id"
                  :label="company.company_name"
                  :value="company.id"
                />
              </el-select>
              <el-select
                v-model="selectedBillContactId"
                clearable
                filterable
                placeholder="选择联系人"
                class="document-input"
                @change="applyContact('bill')"
              >
                <el-option
                  v-for="contact in billContactOptions"
                  :key="contact.id"
                  :label="`${contact.full_name} - ${contact.company_name}`"
                  :value="contact.id"
                />
              </el-select>
              <el-input v-model="billTo.name" placeholder="Contact name" class="document-input" />
              <el-input v-model="billTo.company" placeholder="Company" class="document-input" />
              <el-input v-model="billTo.address" type="textarea" :rows="2" placeholder="Billing address" class="document-input" />
            </div>

            <div class="address-panel">
              <div class="panel-heading">
                <h3>SHIP TO</h3>
                <el-button link size="small" @click="duplicateShipTo">复制 Bill To</el-button>
              </div>
              <el-select
                v-model="selectedShipCompanyId"
                clearable
                filterable
                placeholder="选择已有收货公司"
                class="document-input"
                @change="applyCompany('ship')"
              >
                <el-option
                  v-for="company in customerCompanies"
                  :key="company.id"
                  :label="company.company_name"
                  :value="company.id"
                />
              </el-select>
              <el-select
                v-model="selectedShipContactId"
                clearable
                filterable
                placeholder="选择收货联系人"
                class="document-input"
                @change="applyContact('ship')"
              >
                <el-option
                  v-for="contact in shipContactOptions"
                  :key="contact.id"
                  :label="`${contact.full_name} - ${contact.company_name}`"
                  :value="contact.id"
                />
              </el-select>
              <el-input v-model="shipTo.name" placeholder="Contact name" class="document-input" />
              <el-input v-model="shipTo.company" placeholder="Company" class="document-input" />
              <el-input v-model="shipTo.address" type="textarea" :rows="2" placeholder="Shipping address" class="document-input" />
            </div>

            <div class="date-panel">
              <label>Quote Date</label>
              <el-date-picker v-model="quoteDate" value-format="YYYY-MM-DD" type="date" class="date-control" />
              <label>Valid For</label>
              <el-input-number v-model="validDays" :min="1" :max="180" class="days-control" />
              <p><strong>Valid Till:</strong> {{ validTill }}</p>
            </div>
          </div>
        </section>

        <section class="product-composer">
          <div class="composer-title">
            <div>
              <h3>添加报价产品</h3>
              <p>只选择客户感兴趣的产品；每个产品会加入完整数量区间报价表，不需要填写参考数量。</p>
            </div>
            <el-tag effect="plain">内部报价编辑</el-tag>
          </div>
          <div class="composer-controls">
            <el-select v-model="selectedProductId" filterable placeholder="选择产品" :loading="loadingProducts">
              <el-option
                v-for="p in products"
                :key="p.id"
                :label="productOptionLabel(p)"
                :value="p.id"
                :disabled="addedProductIds.has(p.id)"
              />
            </el-select>
            <el-button type="primary" :disabled="!selectedProductId || selectedProductAlreadyAdded" @click="addProductBlock">
              添加产品
            </el-button>
          </div>
        </section>

        <section class="quote-table">
          <div class="quote-table-head">
            <div>Products</div>
            <div>Quantity</div>
            <div>FOB Unit Price</div>
            <div>DDP Unit Price</div>
            <div>Review</div>
          </div>

          <el-empty v-if="!blocks.length" description="请选择客户感兴趣的产品。系统会按产品生成完整阶梯报价，而不是只生成一个数量点。" />

          <article v-for="block in blocks" :key="block.local_id" class="product-block">
            <div class="product-card">
              <div class="product-title">
                <strong>{{ block.product.internal_sku }}</strong>
                <span>{{ productDisplayName(block.product) }}</span>
              </div>
              <img v-if="productImage(block.product)" :src="productImage(block.product)" alt="Product image" />
              <div v-else class="image-pending">Product image pending</div>
              <p>{{ warningText(block) }}</p>
            </div>

            <div class="tier-table">
              <template v-for="row in block.rows" :key="`${block.local_id}-${row.quantity_label}`">
                <div class="qty-cell">{{ formatQuantityLabel(row.quantity_label) }}</div>
                <div class="price-cell">
                  <el-input v-model="row.fob_unit_price" placeholder="N/A" @change="block.interval_overridden = true" />
                </div>
                <div class="price-cell">
                  <el-input v-model="row.ddp_unit_price" placeholder="N/A" @change="block.interval_overridden = true" />
                </div>
                <div class="review-cell">
                  <el-tag v-if="!hasPrice(row)" type="danger" effect="plain" size="small">缺价格</el-tag>
                </div>
              </template>
            </div>

            <div class="line-tools">
              <el-button type="danger" plain @click="removeBlock(block.local_id)">删除产品</el-button>
            </div>
          </article>
        </section>

        <footer class="quote-closing">
          <el-input v-model="thankYouText" class="thank-you-input" />
          <section class="terms-instructions">
            <h3>Terms &amp; Instructions</h3>

            <div class="terms-layout">
              <div class="terms-preview">
                <div class="terms-section">
                  <h4>Payment Terms:</h4>
                  <p v-for="line in paymentLines" :key="line">{{ line }}</p>
                </div>

                <div class="terms-section compact">
                  <h4>Manufacturing Lead Time</h4>
                  <p>{{ manufacturingLeadTime }}</p>
                </div>

                <div class="terms-section compact">
                  <h4>DDP Delivery Time:</h4>
                  <p>{{ ddpDeliveryTime }}</p>
                </div>

                <div class="terms-section">
                  <h4>Shipping Information:</h4>
                  <p v-for="line in shippingLines" :key="line">{{ line }}</p>
                </div>

                <div class="terms-section">
                  <h4>Additional Notes:</h4>
                  <p v-for="line in additionalLines" :key="line">{{ line }}</p>
                </div>
              </div>

              <div class="terms-editor">
                <h4>编辑英文报价收尾内容</h4>
                <label>Payment Terms</label>
                <el-input v-model="paymentTermsText" type="textarea" :rows="4" />
                <label>Manufacturing Lead Time</label>
                <el-input v-model="manufacturingLeadTime" />
                <label>DDP Delivery Time</label>
                <el-input v-model="ddpDeliveryTime" />
                <label>Shipping Information</label>
                <el-input v-model="shippingInformationText" type="textarea" :rows="5" />
                <label>Additional Notes</label>
                <el-input v-model="additionalNotesText" type="textarea" :rows="5" />
              </div>
            </div>
          </section>
        </footer>
      </div>
    </section>
  </div>
</template>

<style scoped>
.quote-editor-page {
  --quote-accent: #3b82f6;
  --quote-accent-dark: #2563eb;
  --quote-accent-soft: #e8f1ff;
  min-height: 100%;
  padding: 18px 28px 48px;
  background: #f4f6fa;
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 16px;
}

.topbar h1 {
  margin: 8px 0 6px;
  font-size: 28px;
  line-height: 1.1;
}

.topbar p {
  margin: 0;
  color: #7b8494;
}

.topbar-actions {
  display: flex;
  gap: 14px;
}

.notice {
  max-width: 1900px;
  margin: 0 auto 18px;
}

.quote-shell {
  overflow-x: auto;
  padding-bottom: 20px;
}

.quote-paper {
  width: 1340px;
  min-height: 1600px;
  margin: 0 auto;
  padding: 58px 72px 72px;
  background: #fff;
  color: #111827;
  box-shadow: 0 18px 48px rgb(15 23 42 / 12%);
}

.paper-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 28px;
  min-height: 150px;
}

.brand-block {
  flex: 1;
  padding: 10px 0 0 28px;
  border-left: 1px solid #d7e0ea;
}

.brand-block h2 {
  margin: 0 0 8px;
  color: var(--quote-accent);
  font-size: 30px;
  font-weight: 500;
}

.brand-block p {
  margin: 4px 0;
  font-size: 20px;
}

.brand-block a {
  display: inline-block;
  margin: 8px 0;
  color: var(--quote-accent-dark);
  font-size: 19px;
}

.brand-lockup {
  width: 188px;
  flex: 0 0 188px;
  align-self: flex-start;
  padding-top: 0;
  text-align: center;
}

.brand-lockup img {
  width: 128px;
  height: 128px;
  object-fit: contain;
}

.header-quote-card {
  min-width: 230px;
  margin-top: 8px;
  padding: 18px 22px;
  text-align: right;
  border-left: 1px solid #d7e0ea;
}

.header-quote-card span {
  display: block;
  color: #6b7280;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 3px;
}

.header-quote-card strong {
  display: block;
  margin-top: 8px;
  color: var(--quote-accent);
  font-size: 26px;
  line-height: 1.15;
}

.customer-block {
  display: block;
  margin-top: 26px;
}

.address-grid {
  display: grid;
  grid-template-columns: minmax(320px, 1fr) minmax(320px, 1fr) 250px;
  gap: 34px;
}

.address-panel,
.date-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #d5d8dd;
}

.address-panel h3 {
  margin: 0 0 8px;
  padding-bottom: 8px;
  color: var(--quote-accent);
  font-size: 16px;
  font-weight: 700;
  border-bottom: 1px solid #d5d8dd;
}

.panel-heading h3 {
  margin: 0;
  border-bottom: 0;
}

.date-panel label {
  font-size: 16px;
  font-weight: 700;
}

.date-panel p {
  margin: 8px 0 0;
  font-size: 18px;
}

.date-control,
.days-control {
  width: 100%;
}

.document-input :deep(.el-input__wrapper),
.document-input :deep(.el-textarea__inner) {
  border-radius: 3px;
  box-shadow: 0 0 0 1px #dce1e8 inset;
  background: #fff;
}

.product-composer {
  margin: 40px 0 24px;
  padding: 16px 18px;
  border: 1px solid #dde2ea;
  background: #fbfcfe;
}

.composer-title {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 12px;
}

.composer-title h3 {
  margin: 0 0 4px;
  font-size: 18px;
}

.composer-title p {
  margin: 0;
  color: #818a99;
}

.composer-controls {
  display: grid;
  grid-template-columns: minmax(420px, 1fr) 120px;
  gap: 10px;
}

.quote-table {
  border: 1px solid #c8cdd6;
}

.quote-table-head {
  display: grid;
  grid-template-columns: minmax(390px, 1.45fr) 160px 180px 180px 120px;
  background: var(--quote-accent);
  color: #fff;
  font-size: 17px;
  font-weight: 700;
}

.quote-table-head > div {
  padding: 10px 12px;
}

.product-block {
  display: grid;
  grid-template-columns: minmax(390px, 1.45fr) minmax(640px, 2fr);
  border-top: 2px solid #1f2937;
}

.product-card {
  min-height: 264px;
  padding: 14px 16px;
  border-right: 1px solid #c8cdd6;
}

.product-title {
  display: flex;
  gap: 8px;
  align-items: baseline;
  margin-bottom: 12px;
  font-size: 17px;
}

.product-title strong {
  font-weight: 800;
}

.product-card img,
.image-pending {
  width: 78%;
  height: 160px;
  margin: 0 auto 10px;
  display: block;
  object-fit: contain;
}

.image-pending {
  display: grid;
  place-items: center;
  color: #7a8290;
  border: 1px dashed #cfd4dc;
  background: #f8fafc;
}

.product-card p {
  margin: 0;
  color: #7a8290;
  font-size: 12px;
}

.tier-table {
  display: grid;
  grid-template-columns: 160px 180px 180px 1fr;
}

.tier-table > div {
  min-height: 52px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  border-right: 1px solid #d5d9e0;
  border-bottom: 1px solid #d5d9e0;
}

.qty-cell {
  justify-content: center;
  font-size: 17px;
}

.price-cell :deep(.el-input__wrapper) {
  min-height: 36px;
  border-radius: 2px;
  box-shadow: 0 0 0 1px transparent inset;
  background: transparent;
}

.price-cell :deep(.el-input__wrapper:hover),
.price-cell :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--quote-accent) inset;
  background: #fff;
}

.price-cell :deep(.el-input__inner) {
  text-align: right;
  font-size: 16px;
}

.review-cell {
  justify-content: center;
}

.line-tools {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  border-top: 1px solid #dde2ea;
}

.line-tools span {
  margin-right: auto;
  color: #6b7280;
  font-size: 13px;
}

.quote-closing {
  margin-top: 34px;
  border-top: 1px solid #1f2937;
}

.thank-you-input {
  display: block;
  width: min(860px, 92%);
  margin: 28px auto 30px;
}

.thank-you-input :deep(.el-input__wrapper) {
  min-height: 44px;
  border-radius: 2px;
  box-shadow: none;
  background: transparent;
}

.thank-you-input :deep(.el-input__inner) {
  text-align: center;
  color: #000;
  font-size: 22px;
  font-weight: 700;
}

.terms-instructions {
  color: #172236;
  border-top: 1px solid #a8a8a8;
}

.terms-instructions h3 {
  margin: -27px 0 12px;
  width: fit-content;
  padding-right: 12px;
  color: var(--quote-accent);
  background: #fff;
  font-size: 20px;
  font-weight: 800;
}

.terms-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 390px;
  gap: 28px;
}

.terms-section {
  margin-bottom: 24px;
}

.terms-section h4 {
  margin: 0 0 2px;
  font-size: 20px;
  font-weight: 800;
}

.terms-section p {
  margin: 0;
  font-size: 19px;
  line-height: 1.28;
}

.terms-editor {
  padding: 14px;
  border: 1px solid #dbeafe;
  background: #f8fbff;
}

.terms-editor h4 {
  margin: 0 0 12px;
  color: var(--quote-accent-dark);
  font-size: 15px;
}

.terms-editor label {
  display: block;
  margin: 10px 0 4px;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

@media (max-width: 1180px) {
  .topbar,
  .address-grid,
  .quote-closing,
  .terms-layout {
    display: grid;
    grid-template-columns: 1fr;
  }

  .quote-paper {
    width: 980px;
    padding: 42px;
  }

  .composer-controls,
  .product-block,
  .tier-table {
    grid-template-columns: 1fr;
  }
}
</style>
