<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  fetchCatalogProducts,
  postPricingPreview,
  type CatalogProduct,
  type IntervalQuoteRow,
} from '@/api/quoteCatalog'
import { http } from '@/api/http'

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
}

const router = useRouter()

const products = ref<CatalogProduct[]>([])
const selectedProductId = ref('')
const addQuantity = ref(50)
const addIncoterm = ref<'FOB' | 'DDP'>('DDP')
const addStrategy = ref('volume')
const blocks = ref<QuoteProductBlock[]>([])
const loadingProducts = ref(false)
const creating = ref(false)
const error = ref('')

const quoteDate = ref(new Date().toISOString().slice(0, 10))
const validDays = ref(21)
const billTo = ref({
  name: '',
  company: '',
  address: '',
})
const shipTo = ref({
  name: '',
  company: '',
  address: '',
})
const terms = ref(
  'Prices are quoted in USD and are subject to final confirmation before order release. This quote does not reserve inventory or guarantee certification, lead time, or delivery date.',
)
const instructions = ref(
  'Please confirm selected products, quantity tier, shipping term, billing information, and ship-to address before purchase order submission.',
)

const selectedProduct = computed(() => products.value.find((item) => item.id === selectedProductId.value) ?? null)
const validTill = computed(() => {
  const date = new Date(`${quoteDate.value}T00:00:00`)
  date.setDate(date.getDate() + validDays.value)
  return date.toLocaleDateString('en-US')
})
const canCreate = computed(() => blocks.value.length > 0 && !creating.value)

function productImage(product: CatalogProduct) {
  return product.image_url || ''
}

function displayPrice(value: string | null | undefined) {
  return value && value !== 'N/A' ? `$${Number(value).toFixed(2)}` : 'N/A'
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
  return block.rows.map((row) => ({
    min_qty: row.min_qty,
    max_qty: row.max_qty,
    quantity_label: row.quantity_label,
    currency: row.currency || 'USD',
    fob_unit_price: row.fob_unit_price || null,
    ddp_unit_price: row.ddp_unit_price || null,
  }))
}

function selectedUnitPrice(block: QuoteProductBlock) {
  const row =
    block.rows.find((item) => {
      const max = item.max_qty ?? Number.POSITIVE_INFINITY
      return block.quantity >= item.min_qty && block.quantity <= max
    }) || block.rows[0]
  if (!row) return 'N/A'
  return block.incoterm === 'DDP' ? displayPrice(row.ddp_unit_price) : displayPrice(row.fob_unit_price)
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
  error.value = ''
  const localId = `${product.id}-${Date.now()}`
  const block: QuoteProductBlock = {
    local_id: localId,
    product_id: product.id,
    quantity: addQuantity.value,
    incoterm: addIncoterm.value,
    pricing_strategy: addStrategy.value,
    product,
    rows: [],
    loading: true,
    source: '',
    warnings: [],
    cost_model: {},
  }
  blocks.value.push(block)
  try {
    const preview = await postPricingPreview({
      product_id: product.id,
      quantity: addQuantity.value,
      incoterm: addIncoterm.value,
      pricing_strategy: addStrategy.value,
    })
    const stage = preview.quote_model?.final_quote_stage as { interval_quote_table?: IntervalQuoteRow[] } | undefined
    const target = blocks.value.find((item) => item.local_id === localId)
    if (!target) return
    target.rows = normalizeRows(stage?.interval_quote_table || [])
    target.source = preview.source
    target.warnings = preview.warnings || []
    target.cost_model = preview.cost_breakdown || {}
    if (!target.rows.length) {
      error.value = '该产品没有可用区间价，请先维护成本模型或价格区间。'
    }
  } catch (e: unknown) {
    blocks.value = blocks.value.filter((item) => item.local_id !== localId)
    error.value = e instanceof Error ? e.message : '区间报价加载失败，请检查产品成本、物流、汇率或区间价格。'
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
}

async function createQuote() {
  if (!blocks.value.length) {
    error.value = '请至少添加一个产品。'
    return
  }
  creating.value = true
  error.value = ''
  try {
    const { data } = await http.post('/v1/quotes', {
      line_items: blocks.value.map((block) => ({
        product_id: block.product_id,
        quantity: block.quantity,
        incoterm: block.incoterm,
        pricing_strategy: block.pricing_strategy,
        manual_interval_quote_table: quotePayloadRows(block),
      })),
      bill_to: billTo.value,
      ship_to: shipTo.value,
      payment_terms: terms.value,
      shipping_terms: instructions.value,
      customer_notes: `${terms.value}\n\n${instructions.value}`,
      internal_notes: 'Created from editable quote sheet. Manual interval price overrides require internal review before sending.',
    })
    if (data.ok && data.data?.id) {
      ElMessage.success('报价已保存为内部记录，未自动发送。')
      router.push({ name: 'quote-detail', params: { id: data.data.id } })
    } else {
      error.value = '报价已提交但没有返回报价 ID，请刷新报价列表确认。'
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '创建报价失败。'
  } finally {
    creating.value = false
  }
}

onMounted(loadProducts)
</script>

<template>
  <div class="quote-editor-page">
    <div class="toolbar">
      <div>
        <el-button link @click="router.push({ name: 'quotes' })">返回报价列表</el-button>
        <h1>新建报价单</h1>
        <p>操作系统为中文；客户报价正文保持英文格式。保存只创建内部报价记录，不会自动发送。</p>
      </div>
      <div class="toolbar-actions">
        <el-button @click="router.push({ name: 'pricing-preview' })">底层成本/区间逻辑</el-button>
        <el-button type="primary" :loading="creating" :disabled="!canCreate" @click="createQuote">保存报价</el-button>
      </div>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="安全边界"
      description="报价只会保存内部记录和报价模型快照；不会自动发送邮件、通知客户、承诺库存、认证或交期。成本、利润和物流测算保持内部可见。"
      class="mb"
    />
    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />

    <section class="quote-sheet">
      <header class="sheet-header">
        <div class="brand-block">
          <div class="brand-title">IntelliOpus Engineering x HOSUN</div>
          <div>529 Main Street, Suit 2000, Charlestown, MA, 02129</div>
          <a href="https://www.hosunherstar.com" target="_blank" rel="noreferrer">www.hosunherstar.com</a>
          <div>(928) 679-3822</div>
        </div>
        <div class="logo-block">
          <div class="logo-mark">H</div>
          <strong>HOSUN</strong>
        </div>
      </header>

      <section class="quote-meta">
        <div class="quote-number">QUOTE # AUTO</div>
        <div class="address-section">
          <div class="address-card">
            <h3>BILL TO</h3>
            <el-input v-model="billTo.name" placeholder="Contact name" />
            <el-input v-model="billTo.company" placeholder="Company" />
            <el-input v-model="billTo.address" type="textarea" :rows="2" placeholder="Billing address" />
          </div>
          <div class="address-card">
            <h3>SHIP TO</h3>
            <el-button size="small" @click="duplicateShipTo">复制 Bill To</el-button>
            <el-input v-model="shipTo.name" placeholder="Contact name" />
            <el-input v-model="shipTo.company" placeholder="Company" />
            <el-input v-model="shipTo.address" type="textarea" :rows="2" placeholder="Shipping address" />
          </div>
          <div class="date-card">
            <label>Quote Date</label>
            <el-date-picker v-model="quoteDate" value-format="YYYY-MM-DD" type="date" />
            <label>Valid For</label>
            <el-input-number v-model="validDays" :min="1" :max="180" />
            <div class="valid-till"><strong>Valid Till:</strong> {{ validTill }}</div>
          </div>
        </div>
      </section>

      <section class="add-product-panel">
        <div class="panel-title">
          <h2>添加报价产品</h2>
          <span>每个产品会加入完整数量区间；可在下方直接改客户可见单价。</span>
        </div>
        <div class="add-controls">
          <el-select v-model="selectedProductId" filterable placeholder="选择产品" :loading="loadingProducts">
            <el-option
              v-for="p in products"
              :key="p.id"
              :label="`${p.internal_sku} - ${p.product_name}`"
              :value="p.id"
            />
          </el-select>
          <el-input-number v-model="addQuantity" :min="1" />
          <el-select v-model="addIncoterm">
            <el-option label="FOB" value="FOB" />
            <el-option label="DDP" value="DDP" />
          </el-select>
          <el-select v-model="addStrategy">
            <el-option label="销售" value="volume" />
            <el-option label="引流" value="traffic" />
            <el-option label="利润" value="profit" />
          </el-select>
          <el-button type="primary" @click="addProductBlock">添加产品</el-button>
        </div>
      </section>

      <section class="products-table">
        <div class="table-head">
          <div>Products</div>
          <div>Quantity</div>
          <div>EXW Unit Price</div>
          <div>DDP Unit Price</div>
          <div></div>
        </div>

        <el-empty v-if="!blocks.length" description="请选择客户感兴趣的产品，系统会按产品生成完整阶梯报价。" />

        <article v-for="block in blocks" :key="block.local_id" class="product-block">
          <div class="product-info">
            <strong>{{ block.product.internal_sku }}</strong>
            <span>{{ block.product.product_name }}</span>
            <img v-if="productImage(block.product)" :src="productImage(block.product)" alt="Product image" />
            <div v-else class="image-pending">Product image pending</div>
            <small>Internal source: {{ block.source || 'loading' }} · Reference {{ block.quantity }} {{ block.incoterm }} {{ selectedUnitPrice(block) }}</small>
          </div>
          <div class="tier-grid">
            <template v-for="row in block.rows" :key="`${block.local_id}-${row.quantity_label}`">
              <div class="qty-cell">{{ row.quantity_label.replace('-', ' ~ ') }}</div>
              <div class="price-cell">
                <el-input v-model="row.fob_unit_price" placeholder="N/A" />
              </div>
              <div class="price-cell">
                <el-input v-model="row.ddp_unit_price" placeholder="N/A" />
              </div>
              <div class="row-tools">
                <el-tag v-if="block.quantity >= row.min_qty && block.quantity <= (row.max_qty ?? 99999999)" size="small">
                  校验区间
                </el-tag>
              </div>
            </template>
          </div>
          <div class="block-actions">
            <el-input-number v-model="block.quantity" :min="1" />
            <el-select v-model="block.incoterm">
              <el-option label="FOB" value="FOB" />
              <el-option label="DDP" value="DDP" />
            </el-select>
            <el-button type="danger" plain @click="removeBlock(block.local_id)">删除产品</el-button>
          </div>
        </article>
      </section>

      <footer class="quote-footer">
        <div>
          <h3>Terms</h3>
          <el-input v-model="terms" type="textarea" :rows="4" />
        </div>
        <div>
          <h3>Instructions</h3>
          <el-input v-model="instructions" type="textarea" :rows="4" />
        </div>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.quote-editor-page {
  padding: 16px 24px 40px;
  background: #f5f7fb;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.toolbar h1 {
  margin: 6px 0 4px;
  font-size: 24px;
}

.toolbar p {
  margin: 0;
  color: var(--el-text-color-secondary);
}

.toolbar-actions {
  display: flex;
  gap: 10px;
}

.mb {
  margin-bottom: 16px;
}

.quote-sheet {
  max-width: 1280px;
  margin: 0 auto;
  padding: 48px 64px;
  background: #fff;
  color: #111;
  box-shadow: 0 12px 40px rgb(15 23 42 / 10%);
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  gap: 40px;
  min-height: 150px;
}

.brand-block {
  font-size: 18px;
  line-height: 1.7;
}

.brand-title {
  color: #f07723;
  font-size: 28px;
  line-height: 1.2;
}

.brand-block a {
  color: #2f6dd6;
}

.logo-block {
  width: 220px;
  text-align: center;
  font-size: 34px;
  letter-spacing: 3px;
}

.logo-mark {
  width: 112px;
  height: 112px;
  margin: 0 auto 8px;
  border: 16px solid #f07723;
  border-left-color: #ffc928;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 58px;
  line-height: 1;
}

.quote-meta {
  position: relative;
  margin-top: 12px;
}

.quote-number {
  position: absolute;
  left: -48px;
  top: 0;
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  font-size: 42px;
  letter-spacing: 4px;
  color: #666;
}

.address-section {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) minmax(260px, 1fr) 250px;
  gap: 32px;
  margin-left: 36px;
}

.address-card,
.date-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.address-card h3 {
  margin: 0 0 6px;
  padding-bottom: 8px;
  border-bottom: 1px solid #cfcfcf;
  color: #f07723;
  font-size: 16px;
}

.date-card label {
  font-weight: 700;
}

.valid-till {
  margin-top: 6px;
  font-size: 16px;
}

.add-product-panel {
  margin: 36px 0 20px;
  padding: 16px;
  border: 1px solid #d9dde6;
  background: #fbfcff;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: baseline;
  margin-bottom: 12px;
}

.panel-title h2 {
  margin: 0;
  font-size: 18px;
}

.panel-title span {
  color: var(--el-text-color-secondary);
}

.add-controls {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) 130px 120px 120px auto;
  gap: 10px;
}

.products-table {
  margin-top: 18px;
  border: 1px solid #c8c8c8;
}

.table-head {
  display: grid;
  grid-template-columns: minmax(360px, 1.6fr) 160px 180px 180px 120px;
  background: #f07723;
  color: #fff;
  font-weight: 700;
}

.table-head > div {
  padding: 10px 12px;
}

.product-block {
  display: grid;
  grid-template-columns: minmax(360px, 1.6fr) minmax(520px, 2fr);
  border-top: 2px solid #222;
}

.product-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 190px;
  padding: 14px;
  border-right: 1px solid #c8c8c8;
}

.product-info strong {
  font-size: 16px;
}

.product-info img,
.image-pending {
  flex: 1;
  max-height: 170px;
  object-fit: contain;
  align-self: center;
}

.image-pending {
  width: 70%;
  min-height: 120px;
  display: grid;
  place-items: center;
  color: #777;
  border: 1px dashed #c8c8c8;
  background: #fafafa;
}

.product-info small {
  color: #666;
}

.tier-grid {
  display: grid;
  grid-template-columns: 160px 180px 180px 1fr;
}

.tier-grid > div {
  min-height: 50px;
  padding: 8px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #d7d7d7;
  border-right: 1px solid #d7d7d7;
}

.qty-cell {
  justify-content: center;
  font-size: 16px;
}

.price-cell :deep(.el-input__wrapper) {
  box-shadow: none;
  border-radius: 0;
  background: #fff;
}

.price-cell :deep(.el-input__inner) {
  text-align: right;
}

.row-tools {
  justify-content: center;
}

.block-actions {
  grid-column: 1 / -1;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding: 10px 12px;
  background: #f8f8f8;
}

.quote-footer {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 28px;
}

.quote-footer h3 {
  margin: 0 0 8px;
  color: #f07723;
}

@media (max-width: 1100px) {
  .quote-sheet {
    padding: 32px 24px;
  }

  .sheet-header,
  .toolbar,
  .address-section,
  .quote-footer {
    grid-template-columns: 1fr;
    display: grid;
  }

  .quote-number {
    position: static;
    writing-mode: horizontal-tb;
    transform: none;
    margin-bottom: 16px;
    font-size: 28px;
  }

  .address-section {
    margin-left: 0;
  }

  .add-controls,
  .product-block,
  .table-head,
  .tier-grid {
    grid-template-columns: 1fr;
  }

  .table-head > div:nth-child(n + 2) {
    display: none;
  }
}
</style>
