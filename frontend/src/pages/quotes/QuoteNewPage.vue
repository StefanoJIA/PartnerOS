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

const DEFAULT_INTERVAL_ROWS: EditableIntervalRow[] = [
  { min_qty: 1, max_qty: 49, quantity_label: '1-49', currency: 'USD', fob_unit_price: '', ddp_unit_price: '' },
  { min_qty: 50, max_qty: 99, quantity_label: '50-99', currency: 'USD', fob_unit_price: '', ddp_unit_price: '' },
  { min_qty: 100, max_qty: 299, quantity_label: '100-299', currency: 'USD', fob_unit_price: '', ddp_unit_price: '' },
  { min_qty: 300, max_qty: 499, quantity_label: '300-499', currency: 'USD', fob_unit_price: '', ddp_unit_price: '' },
  { min_qty: 500, max_qty: null, quantity_label: '>=500', currency: 'USD', fob_unit_price: '', ddp_unit_price: '' },
]

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
const billTo = ref({ name: '', company: '', address: '' })
const shipTo = ref({ name: '', company: '', address: '' })
const terms = ref(
  'Prices are quoted in USD and are subject to final confirmation before order release. This quote does not reserve inventory or guarantee certification, lead time, or delivery date.',
)
const instructions = ref(
  'Please confirm selected products, quantity tier, shipping term, billing information, and ship-to address before purchase order submission.',
)

const selectedProduct = computed(() => products.value.find((item) => item.id === selectedProductId.value) ?? null)
const canCreate = computed(() => blocks.value.length > 0 && !creating.value)
const validTill = computed(() => {
  const date = new Date(`${quoteDate.value}T00:00:00`)
  date.setDate(date.getDate() + validDays.value)
  return date.toLocaleDateString('en-US')
})

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

function displayPrice(value: string | null | undefined) {
  return value && value !== 'N/A' ? `$${Number(value).toFixed(2)}` : 'N/A'
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

function warningText(block: QuoteProductBlock) {
  if (block.source === 'manual_interval_blank') return '需手工填写完整阶梯价'
  if (block.warnings.length) return block.warnings.join(' / ')
  return '已载入底层区间价'
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
  blocks.value.push({
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
  })

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
      target.rows = blankRows()
      target.source = 'manual_interval_blank'
      target.warnings = ['No interval price found; manual customer-visible prices required.']
      error.value = '该产品没有可用区间价，已加入空白阶梯表；请手工填写 EXW/FOB 或 DDP 单价后再保存。'
    }
  } catch (e: unknown) {
    const target = blocks.value.find((item) => item.local_id === localId)
    if (target) {
      target.rows = blankRows()
      target.source = 'manual_interval_blank'
      target.warnings = [e instanceof Error ? e.message : 'Preview failed; manual interval prices required.']
      error.value = '区间报价加载失败，已加入空白阶梯表；请手工填写客户可见单价后再保存。'
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
}

async function createQuote() {
  if (!blocks.value.length) {
    error.value = '请至少添加一个产品。'
    return
  }
  const incomplete = blocks.value.find((block) => block.rows.some((row) => !hasPrice(row)))
  if (incomplete) {
    error.value = `产品 ${incomplete.product.internal_sku} 存在未填写单价的数量区间；每个区间至少需要 EXW/FOB 或 DDP 价格。`
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
    <div class="topbar">
      <div>
        <el-button link @click="router.push({ name: 'quotes' })">返回报价列表</el-button>
        <h1>新建报价单</h1>
        <p>操作系统为中文；客户报价正文保持英文格式。保存只创建内部报价记录，不会自动发送。</p>
      </div>
      <div class="topbar-actions">
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
      class="notice"
    />
    <el-alert v-if="error" type="error" :title="error" show-icon class="notice" />

    <section class="quote-shell">
      <div class="quote-paper">
        <header class="paper-header">
          <div class="brand-block">
            <h2>IntelliOpus Engineering x HOSUN</h2>
            <p>529 Main Street, Suit 2000, Charlestown, MA, 02129</p>
            <a href="https://www.hosunherstar.com" target="_blank" rel="noreferrer">www.hosunherstar.com</a>
            <p>(928) 679-3822</p>
          </div>
          <div class="brand-lockup">
            <strong>HOSUN</strong>
            <span>Brand logo pending</span>
          </div>
        </header>

        <section class="customer-block">
          <aside class="quote-rail">
            <span>QUOTE</span>
            <strong># AUTO</strong>
          </aside>

          <div class="address-grid">
            <div class="address-panel">
              <h3>BILL TO</h3>
              <el-input v-model="billTo.name" placeholder="Contact name" class="document-input" />
              <el-input v-model="billTo.company" placeholder="Company" class="document-input" />
              <el-input v-model="billTo.address" type="textarea" :rows="2" placeholder="Billing address" class="document-input" />
            </div>

            <div class="address-panel">
              <div class="panel-heading">
                <h3>SHIP TO</h3>
                <el-button link size="small" @click="duplicateShipTo">复制 Bill To</el-button>
              </div>
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
              <p>选择客户感兴趣的产品；每个产品会生成完整阶梯价，可直接编辑客户可见单价。</p>
            </div>
            <el-tag effect="plain">Manual quote sheet</el-tag>
          </div>
          <div class="composer-controls">
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

        <section class="quote-table">
          <div class="quote-table-head">
            <div>Products</div>
            <div>Quantity</div>
            <div>EXW Unit Price</div>
            <div>DDP Unit Price</div>
            <div>Internal</div>
          </div>

          <el-empty v-if="!blocks.length" description="请选择客户感兴趣的产品，系统会按产品生成完整阶梯报价。" />

          <article v-for="block in blocks" :key="block.local_id" class="product-block">
            <div class="product-card">
              <div class="product-title">
                <strong>{{ block.product.internal_sku }}</strong>
                <span>{{ block.product.product_name }}</span>
              </div>
              <img v-if="productImage(block.product)" :src="productImage(block.product)" alt="Product image" />
              <div v-else class="image-pending">Product image pending</div>
              <p>{{ warningText(block) }}</p>
            </div>

            <div class="tier-table">
              <template v-for="row in block.rows" :key="`${block.local_id}-${row.quantity_label}`">
                <div class="qty-cell">{{ row.quantity_label.replace('-', ' ~ ') }}</div>
                <div class="price-cell">
                  <el-input v-model="row.fob_unit_price" placeholder="N/A" />
                </div>
                <div class="price-cell">
                  <el-input v-model="row.ddp_unit_price" placeholder="N/A" />
                </div>
                <div class="review-cell">
                  <el-tag v-if="!hasPrice(row)" type="danger" effect="plain" size="small">缺价格</el-tag>
                  <el-tag
                    v-else-if="block.quantity >= row.min_qty && block.quantity <= (row.max_qty ?? 99999999)"
                    type="warning"
                    effect="plain"
                    size="small"
                  >
                    校验区间
                  </el-tag>
                </div>
              </template>
            </div>

            <div class="line-tools">
              <span>内部参考：{{ block.quantity }} {{ block.incoterm }} {{ selectedUnitPrice(block) }}</span>
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
            <el-input v-model="terms" type="textarea" :rows="4" class="document-input" />
          </div>
          <div>
            <h3>Instructions</h3>
            <el-input v-model="instructions" type="textarea" :rows="4" class="document-input" />
          </div>
        </footer>
      </div>
    </section>
  </div>
</template>

<style scoped>
.quote-editor-page {
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
  justify-content: space-between;
  gap: 60px;
  min-height: 172px;
}

.brand-block h2 {
  margin: 0 0 8px;
  color: #f37021;
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
  color: #2d67d6;
  font-size: 19px;
}

.brand-lockup {
  min-width: 210px;
  align-self: flex-start;
  padding-top: 28px;
  text-align: center;
}

.brand-lockup strong {
  display: block;
  font-size: 42px;
  letter-spacing: 4px;
}

.brand-lockup span {
  display: block;
  margin-top: 6px;
  color: #8a92a0;
  font-size: 12px;
  letter-spacing: 0;
}

.customer-block {
  display: grid;
  grid-template-columns: 76px 1fr;
  gap: 28px;
  margin-top: 26px;
}

.quote-rail {
  height: 230px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  color: #5d6470;
  border-right: 1px solid #e0e3e8;
}

.quote-rail span {
  font-size: 44px;
  letter-spacing: 5px;
}

.quote-rail strong {
  color: #f37021;
  font-size: 28px;
  letter-spacing: 2px;
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

.address-panel h3,
.quote-footer h3 {
  margin: 0 0 8px;
  padding-bottom: 8px;
  color: #f37021;
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
  grid-template-columns: minmax(360px, 1fr) 130px 120px 120px 110px;
  gap: 10px;
}

.quote-table {
  border: 1px solid #c8cdd6;
}

.quote-table-head {
  display: grid;
  grid-template-columns: minmax(390px, 1.45fr) 160px 180px 180px 120px;
  background: #f37021;
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
  box-shadow: 0 0 0 1px #8bbcff inset;
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

.quote-footer {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
  margin-top: 30px;
}

@media (max-width: 1180px) {
  .topbar,
  .address-grid,
  .quote-footer {
    display: grid;
    grid-template-columns: 1fr;
  }

  .quote-paper {
    width: 980px;
    padding: 42px;
  }

  .customer-block,
  .composer-controls,
  .product-block,
  .tier-table {
    grid-template-columns: 1fr;
  }

  .quote-rail {
    height: auto;
    min-height: 58px;
    writing-mode: horizontal-tb;
    transform: none;
    border-right: 0;
    border-bottom: 1px solid #e0e3e8;
  }
}
</style>
