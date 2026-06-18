<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchCatalogProducts,
  fetchPricingAssumptions,
  postPricingPreview,
  updateOceanFreightAssumption,
  updateCatalogProduct,
  type CatalogProduct,
  type IntervalQuoteRow,
  type PricingAssumptionSnapshot,
} from '@/api/quoteCatalog'

const loading = ref(false)
const tableLoading = ref(false)
const savingMargin = ref(false)
const error = ref<string | null>(null)
const products = ref<CatalogProduct[]>([])
const category = ref('')
const search = ref('')
const partnerCode = ref('')
const selected = ref<CatalogProduct | null>(null)
const tableDrawer = ref(false)
const intervalRows = ref<IntervalQuoteRow[]>([])
const marginPercentDraft = ref<number | null>(null)
const assumptions = ref<PricingAssumptionSnapshot | null>(null)
const assumptionLoading = ref(false)
const assumptionSaving = ref(false)
const oceanFreightDraft = ref(22)

const partnerOptions = [
  { label: '全部 Partner', value: '' },
  { label: 'HOSUN', value: 'HOSUN' },
  { label: 'JOOBOO', value: 'JOOBOO' },
]

const visibleCategories = computed(() =>
  Array.from(new Set(products.value.map((item) => item.product_category).filter(Boolean))).sort(),
)

const partnerStats = computed(() => {
  const base = new Map<string, number>()
  for (const product of products.value) {
    const key = product.partner_code || product.partner_name || '未归属'
    base.set(key, (base.get(key) || 0) + 1)
  }
  return Array.from(base.entries()).map(([partner, count]) => ({ partner, count }))
})

function text(value: unknown, fallback = '未维护') {
  const raw = String(value ?? '').trim()
  return raw || fallback
}

function money(value: unknown, prefix = '$') {
  if (value === null || value === undefined || value === '') return '未维护'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return String(value)
  return `${prefix}${numeric.toFixed(2)}`
}

function numberText(value: unknown, suffix = '') {
  if (value === null || value === undefined || value === '') return '未维护'
  const numeric = Number(value)
  return Number.isFinite(numeric) ? `${numeric.toFixed(2)}${suffix}` : `${value}${suffix}`
}

function summary(product: CatalogProduct) {
  return product.configuration_summary || {}
}

function pricing(product: CatalogProduct | null) {
  return product?.pricing_model_summary || {}
}

const fxSummary = computed(() => {
  const withFx = products.value.find((item) => pricing(item).fx_rate_usd_cny)
  if (!withFx) return null
  return {
    rate: pricing(withFx).fx_rate_usd_cny,
    date: pricing(withFx).fx_rate_date,
    source: pricing(withFx).fx_source,
    stale: pricing(withFx).fx_is_stale,
  }
})

const oceanFreightDisplay = computed(() => assumptions.value?.ocean_freight || null)

function productImage(product: CatalogProduct) {
  return product.image_url || '/intelliopus-logo.png'
}

function customerName(product: CatalogProduct) {
  const attrs = product.attributes_json || {}
  return String(attrs['customer_quote_name'] || product.product_name)
}

function categoryLabel(value: string | null | undefined) {
  const labels: Record<string, string> = {
    lifting_systems: '升降系统',
    lifting_columns: '升降柱',
    desk_frames: '桌架',
    heavy_duty_supply: '重载升降系统',
    heavy_duty_desk_frames: '重载桌架',
    education_furniture: '教育家具',
    project_furniture: '项目制家具',
    desk_accessories: '配件',
    pneumatic_standing_desks: '气动升降桌',
    benching_frames: '多人位桌架',
    hosun_general: 'HOSUN 产品',
  }
  return value ? labels[value] || value : '未分类'
}

function intervalCount(product: CatalogProduct) {
  return Number(product.quote_interval_count || 0)
}

function rowStatus(product: CatalogProduct) {
  if (product.has_interval_pricing) return { label: '区间报价已维护', type: 'success' as const }
  return { label: '需要维护区间价', type: 'warning' as const }
}

function formatPrice(value: string | null | undefined) {
  if (!value || value === 'N/A') return 'N/A'
  const numeric = Number(value)
  return Number.isFinite(numeric) ? `$${numeric.toFixed(2)}` : value
}

function marginValue(product: CatalogProduct | null) {
  const value = pricing(product).product_target_margin_percent
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await fetchCatalogProducts({
      partner_code: partnerCode.value || undefined,
      category: category.value || undefined,
      search: search.value || undefined,
      limit: 200,
    })
    products.value = data.items
    if (selected.value) {
      selected.value = data.items.find((item) => item.id === selected.value?.id) || selected.value
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '报价产品目录加载失败，请确认 backend 和登录状态。'
  } finally {
    loading.value = false
  }
}

async function loadAssumptions() {
  assumptionLoading.value = true
  try {
    const data = await fetchPricingAssumptions()
    assumptions.value = data
    const numeric = Number(data.ocean_freight.numeric_value)
    oceanFreightDraft.value = Number.isFinite(numeric) ? numeric : 22
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '计价假设加载失败')
  } finally {
    assumptionLoading.value = false
  }
}

async function saveOceanFreightAssumption() {
  if (!Number.isFinite(Number(oceanFreightDraft.value)) || Number(oceanFreightDraft.value) <= 0) {
    ElMessage.error('海运单价必须大于 0')
    return
  }
  assumptionSaving.value = true
  try {
    assumptions.value = await updateOceanFreightAssumption({
      ocean_freight_unit_price: Number(oceanFreightDraft.value),
      source: 'manual_provider_quote',
      notes: 'Updated from internal quote catalog assumptions panel.',
    })
    ElMessage.success('海运单价已保存，产品成本与区间报价会按最新假设重新计算。')
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '海运单价保存失败')
  } finally {
    assumptionSaving.value = false
  }
}

async function openIntervalTable(product: CatalogProduct) {
  selected.value = product
  marginPercentDraft.value = marginValue(product)
  tableDrawer.value = true
  intervalRows.value = []
  tableLoading.value = true
  try {
    const result = await postPricingPreview({
      product_id: product.id,
      quantity: 50,
      incoterm: 'DDP',
      pricing_strategy: 'volume',
    })
    intervalRows.value = (result.quote_model?.final_quote_stage?.interval_quote_table as IntervalQuoteRow[]) || []
  } catch {
    intervalRows.value = []
  } finally {
    tableLoading.value = false
  }
}

async function saveMargin() {
  if (!selected.value || marginPercentDraft.value === null) return
  savingMargin.value = true
  try {
    const attrs = { ...(selected.value.attributes_json || {}) }
    attrs.target_margin = Number(marginPercentDraft.value) / 100
    attrs.quote_markup_multiplier = 1 + Number(marginPercentDraft.value) / 100
    attrs.pricing_margin_source = 'manual_catalog_review'
    await updateCatalogProduct(selected.value.id, { attributes_json: attrs })
    ElMessage.success('产品级利润率已保存到内部计价模型。已有固定区间价不会被自动覆盖。')
    await load()
    if (selected.value) {
      const refreshed = products.value.find((item) => item.id === selected.value?.id)
      if (refreshed) selected.value = refreshed
    }
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '利润率保存失败')
  } finally {
    savingMargin.value = false
  }
}

function clearFilters() {
  partnerCode.value = ''
  category.value = ''
  search.value = ''
  load()
}

onMounted(() => {
  loadAssumptions()
  load()
})
</script>

<template>
  <div class="catalog-page">
    <section class="catalog-hero">
      <div>
        <p class="eyebrow">Product Catalog / Quote Source</p>
        <h1>报价产品目录</h1>
        <p class="hero-copy">
          这里是内部报价选品和计价模型入口。每个产品应维护完整数量区间；客户报价单只展示区间单价，
          出厂成本、重量、海运单价、汇率、利润率和物流测算只在内部可见。
        </p>
      </div>
      <div class="hero-metrics">
        <div>
          <span>{{ products.length }}</span>
          <small>当前结果</small>
        </div>
        <div>
          <span>{{ products.filter((item) => item.has_interval_pricing).length }}</span>
          <small>已有区间价</small>
        </div>
        <div>
          <span>{{ products.filter((item) => item.image_url).length }}</span>
          <small>已有图片</small>
        </div>
      </div>
    </section>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb-4"
      title="安全边界：报价目录只用于内部选品、成本模型和区间价维护；不会自动创建报价、不会自动发送、不会承诺库存。"
    />

    <section class="assumption-panel">
      <div>
        <p class="eyebrow">Pricing Assumptions / 内部计价假设</p>
        <h2>汇率与海运单价</h2>
        <p>
          海运单价和汇率在这里作为独立假设维护。产品成本按“固定人民币成本 + 重量 × 海运单价”计算到美国 DDP 成本；
          利润率只在报价区间阶段使用，不会写入客户可见成本。
        </p>
      </div>
      <div class="assumption-cards">
        <div class="assumption-card">
          <span>海运单价</span>
          <strong>{{ oceanFreightDisplay ? numberText(oceanFreightDisplay.numeric_value, ` ${oceanFreightDisplay.unit || 'RMB/kg'}`) : '22.00 RMB/kg' }}</strong>
          <small>来源：{{ oceanFreightDisplay?.source || 'manual_provider_quote' }}</small>
          <div class="assumption-edit">
            <el-input-number v-model="oceanFreightDraft" :min="0.01" :precision="2" :step="1" :disabled="assumptionLoading" />
            <el-button type="primary" :loading="assumptionSaving" @click="saveOceanFreightAssumption">保存</el-button>
          </div>
        </div>
        <div class="assumption-card">
          <span>实时汇率 USD/CNY</span>
          <strong>{{ fxSummary ? numberText(fxSummary.rate) : '未加载' }}</strong>
          <small>
            {{ fxSummary ? `${fxSummary.date || '无日期'} / ${fxSummary.source || 'unknown'}` : '来自后台 fx_rates 最新记录' }}
          </small>
          <el-tag v-if="fxSummary?.stale" type="warning" effect="plain">汇率可能过期</el-tag>
        </div>
        <div class="assumption-card safety">
          <span>安全边界</span>
          <strong>Internal Only</strong>
          <small>不自动发送，不改变 quote/order 状态，不记录 raw token，不向客户暴露成本/利润。</small>
        </div>
      </div>
    </section>

    <section class="toolbar">
      <el-segmented v-model="partnerCode" :options="partnerOptions" @change="load" />
      <el-select v-model="category" clearable placeholder="分类筛选" class="w-56" @change="load">
        <el-option v-for="item in visibleCategories" :key="item" :label="categoryLabel(item)" :value="item" />
      </el-select>
      <el-input v-model="search" clearable placeholder="搜索 SKU / 产品名称 / 规格" class="w-80" @keyup.enter="load" />
      <el-button type="primary" @click="load">刷新</el-button>
      <el-button @click="clearFilters">清空</el-button>
    </section>

    <div class="partner-strip">
      <el-tag v-for="item in partnerStats" :key="item.partner" effect="plain">
        {{ item.partner }} · {{ item.count }} 个产品
      </el-tag>
      <el-tag type="success" effect="plain">HOSUN / JOOBOO 平级合作伙伴</el-tag>
    </div>

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />

    <el-table v-loading="loading" :data="products" stripe class="catalog-table" row-key="id">
      <el-table-column label="产品" min-width="390">
        <template #default="{ row }">
          <div class="product-cell">
            <img :src="productImage(row)" alt="" />
            <div>
              <div class="product-title">{{ customerName(row) }}</div>
              <div class="product-meta">{{ row.internal_sku }} · 原厂型号 {{ row.partner_product_code || '未维护' }}</div>
              <div class="mt-2 flex flex-wrap gap-1">
                <el-tag size="small" effect="plain">{{ row.partner_code || row.partner_name || '未归属' }}</el-tag>
                <el-tag size="small" type="info" effect="plain">{{ categoryLabel(row.product_family || row.product_category) }}</el-tag>
                <el-tag v-if="!row.image_url" size="small" type="warning" effect="plain">图片待补</el-tag>
              </div>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="规格参数" min-width="260">
        <template #default="{ row }">
          <div class="config-grid">
            <span>类型：{{ text(summary(row).base_type) }}</span>
            <span>节数：{{ text(summary(row).stage) }}</span>
            <span>尺寸：{{ text(summary(row).dimensions) }}</span>
            <span>承重：{{ text(summary(row).load_capacity) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="内部计价模型" min-width="300">
        <template #default="{ row }">
          <div class="pricing-grid">
            <span>汇率 USD/CNY：{{ numberText(pricing(row).fx_rate_usd_cny) }}</span>
            <span>出厂成本：{{ money(pricing(row).factory_cost_rmb, '¥') }}</span>
            <span>重量：{{ numberText(pricing(row).unit_weight_kg, ' kg') }}</span>
            <span>海运单价：{{ money(pricing(row).ocean_freight_unit_price, '¥') }}</span>
            <span>目标利润率：{{ numberText(pricing(row).product_target_margin_percent, '%') }}</span>
            <el-tag v-if="pricing(row).fx_is_stale" size="small" type="warning" effect="plain">汇率可能过期</el-tag>
            <el-tag v-if="!pricing(row).has_cost_model" size="small" type="danger" effect="plain">成本模型缺失</el-tag>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="区间报价状态" width="180">
        <template #default="{ row }">
          <el-tag :type="rowStatus(row).type" effect="plain">{{ rowStatus(row).label }}</el-tag>
          <p class="mt-2 text-xs text-slate-500">{{ intervalCount(row) }} 条区间价格</p>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openIntervalTable(row)">查看/编辑模型</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && !error && !products.length" description="暂无产品。请运行产品导入脚本或调整筛选条件。" />

    <el-drawer v-model="tableDrawer" size="680px" :title="selected ? customerName(selected) : '产品详情'">
      <div v-if="selected" class="drawer-body">
        <img class="drawer-image" :src="productImage(selected)" alt="" />

        <div class="drawer-section">
          <h3>产品配置</h3>
          <dl>
            <dt>Partner</dt><dd>{{ selected.partner_code || selected.partner_name || '未归属' }}</dd>
            <dt>IntelliOpus SKU</dt><dd>{{ selected.internal_sku }}</dd>
            <dt>原厂型号</dt><dd>{{ selected.partner_product_code || '未维护' }}</dd>
            <dt>产品族</dt><dd>{{ categoryLabel(selected.product_family || selected.product_category) }}</dd>
            <dt>配置来源</dt><dd>{{ text(summary(selected).source_system) }}</dd>
          </dl>
        </div>

        <div class="drawer-section">
          <h3>内部计价参数</h3>
          <dl>
            <dt>最新汇率</dt>
            <dd>
              USD/CNY {{ numberText(pricing(selected).fx_rate_usd_cny) }}
              <span class="muted">({{ text(pricing(selected).fx_rate_date) }} · {{ text(pricing(selected).fx_source) }})</span>
            </dd>
            <dt>出厂成本</dt><dd>{{ money(pricing(selected).factory_cost_rmb, '¥') }}</dd>
            <dt>单位重量</dt><dd>{{ numberText(pricing(selected).unit_weight_kg, ' kg') }}</dd>
            <dt>海运单价</dt><dd>{{ money(pricing(selected).ocean_freight_unit_price, '¥') }}</dd>
            <dt>FOB 成本</dt><dd>{{ money(pricing(selected).fob_cost_usd) }}</dd>
            <dt>DDP 成本</dt><dd>{{ money(pricing(selected).ddp_cost_usd) }}</dd>
            <dt>目标利润率</dt>
            <dd class="margin-edit">
              <el-input-number v-model="marginPercentDraft" :min="0" :max="300" :precision="2" />
              <span>%</span>
              <el-button size="small" type="primary" :loading="savingMargin" @click="saveMargin">保存利润率</el-button>
            </dd>
          </dl>
          <p class="model-note">
            利润率用于成本模型生成区间价；如产品已有从 Excel 价目表导入的固定区间价，系统不会自动覆盖历史客户报价区间。
          </p>
        </div>

        <div class="drawer-section">
          <h3>客户可见区间报价表</h3>
          <el-table v-loading="tableLoading" :data="intervalRows" size="small" border>
            <el-table-column prop="quantity_label" label="Quantity" width="120" />
            <el-table-column label="FOB Unit Price">
              <template #default="{ row }">{{ formatPrice(row.fob_unit_price) }}</template>
            </el-table-column>
            <el-table-column label="DDP Unit Price">
              <template #default="{ row }">{{ formatPrice(row.ddp_unit_price) }}</template>
            </el-table-column>
          </el-table>
          <p v-if="!tableLoading && !intervalRows.length" class="mt-3 text-sm text-amber-700">
            该产品还没有可用区间报价。请先维护成本模型或 ProductPriceTier。
          </p>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.catalog-page {
  color: #152238;
}

.catalog-hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 18px;
  padding: 22px;
  border: 1px solid #bfdbfe;
  background: #ffffff;
}

.eyebrow {
  margin: 0 0 6px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.catalog-hero h1 {
  margin: 0;
  color: #0f172a;
  font-size: 26px;
  font-weight: 760;
}

.hero-copy {
  max-width: 880px;
  margin: 10px 0 0;
  color: #526174;
  line-height: 1.7;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(92px, 1fr));
  gap: 10px;
  align-self: start;
}

.hero-metrics div {
  min-width: 92px;
  padding: 12px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  text-align: center;
}

.hero-metrics span {
  display: block;
  color: #1d4ed8;
  font-size: 24px;
  font-weight: 760;
}

.hero-metrics small {
  color: #64748b;
}

.assumption-panel {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(520px, 1.5fr);
  gap: 18px;
  margin-bottom: 16px;
  padding: 18px;
  border: 1px solid #bfdbfe;
  background: #f8fbff;
}

.assumption-panel h2 {
  margin: 0;
  color: #0f172a;
  font-size: 20px;
  font-weight: 740;
}

.assumption-panel p {
  margin: 8px 0 0;
  color: #526174;
  line-height: 1.65;
}

.assumption-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.assumption-card {
  display: grid;
  gap: 8px;
  align-content: start;
  min-height: 126px;
  padding: 12px;
  border: 1px solid #dbeafe;
  background: #fff;
}

.assumption-card span {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.assumption-card strong {
  color: #1d4ed8;
  font-size: 22px;
  line-height: 1.15;
}

.assumption-card small {
  color: #64748b;
  line-height: 1.45;
}

.assumption-card.safety strong {
  color: #0f172a;
}

.assumption-edit {
  display: flex;
  gap: 8px;
  align-items: center;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.partner-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.product-cell {
  display: flex;
  align-items: center;
  gap: 14px;
}

.product-cell img {
  width: 92px;
  height: 70px;
  object-fit: contain;
  border: 1px solid #dbeafe;
  background: #fff;
}

.product-title {
  color: #0f172a;
  font-weight: 720;
  line-height: 1.35;
}

.product-meta {
  margin-top: 4px;
  color: #64748b;
  font-size: 12px;
}

.config-grid,
.pricing-grid {
  display: grid;
  gap: 4px;
  color: #475569;
  font-size: 13px;
}

.drawer-body {
  display: grid;
  gap: 18px;
}

.drawer-image {
  width: 100%;
  max-height: 260px;
  object-fit: contain;
  border: 1px solid #bfdbfe;
  background: #fff;
}

.drawer-section {
  border-top: 1px solid #e2e8f0;
  padding-top: 14px;
}

.drawer-section h3 {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 720;
}

dl {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 8px 12px;
  margin: 0;
  font-size: 14px;
}

dt {
  color: #64748b;
}

dd {
  margin: 0;
  color: #0f172a;
}

.margin-edit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-note,
.muted {
  color: #64748b;
  font-size: 12px;
}
</style>
