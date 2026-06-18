<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchCatalogProducts, postPricingPreview, type CatalogProduct, type IntervalQuoteRow } from '@/api/quoteCatalog'

const loading = ref(false)
const tableLoading = ref(false)
const error = ref<string | null>(null)
const products = ref<CatalogProduct[]>([])
const category = ref('')
const search = ref('')
const partnerCode = ref('')
const selected = ref<CatalogProduct | null>(null)
const tableDrawer = ref(false)
const intervalRows = ref<IntervalQuoteRow[]>([])

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

function summary(product: CatalogProduct) {
  return product.configuration_summary || {}
}

function productImage(product: CatalogProduct) {
  return product.image_url || '/favicon.svg'
}

function customerName(product: CatalogProduct) {
  const attrs = product.attributes_json || {}
  return String(attrs['customer_quote_name'] || product.product_name)
}

function categoryLabel(value: string | null) {
  const labels: Record<string, string> = {
    lifting_systems: '升降系统',
    lifting_columns: '升降柱',
    desk_frames: '桌架',
    heavy_duty_supply: '重载系统',
    education_furniture: '教育家具',
    project_furniture: '项目制家具',
    desk_accessories: '配件',
    pneumatic_standing_desks: '气动升降桌',
    benching_frames: '多人位桌架',
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
  } catch (e) {
    error.value = e instanceof Error ? e.message : '报价产品目录加载失败，请确认 backend 和登录状态。'
  } finally {
    loading.value = false
  }
}

async function openIntervalTable(product: CatalogProduct) {
  selected.value = product
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

function clearFilters() {
  partnerCode.value = ''
  category.value = ''
  search.value = ''
  load()
}

onMounted(load)
</script>

<template>
  <div class="catalog-page">
    <section class="catalog-hero">
      <div>
        <p class="eyebrow">Product Catalog / Quote Source</p>
        <h1>报价产品目录</h1>
        <p class="hero-copy">
          这里是报价单选品来源。每个产品都应维护完整数量区间，报价单会展示该产品所有区间价格；
          下单后才根据实际数量形成订单总价。成本、利润和物流测算仍保持内部可见。
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
      title="安全边界：报价目录只用于内部选品和区间价维护，不自动创建报价、不自动发送、不承诺库存。"
    />

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
      <el-table-column label="产品" min-width="380">
        <template #default="{ row }">
          <div class="product-cell">
            <img :src="productImage(row)" alt="" />
            <div>
              <div class="product-title">{{ customerName(row) }}</div>
              <div class="product-meta">{{ row.internal_sku }} · 原 SKU {{ row.partner_product_code || '未维护' }}</div>
              <div class="mt-2 flex flex-wrap gap-1">
                <el-tag size="small" effect="plain">{{ row.partner_code || row.partner_name || '未归属' }}</el-tag>
                <el-tag size="small" type="info" effect="plain">{{ categoryLabel(row.product_family || row.product_category) }}</el-tag>
                <el-tag v-if="!row.image_url" size="small" type="warning" effect="plain">图片待补</el-tag>
              </div>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="配置逻辑" min-width="260">
        <template #default="{ row }">
          <div class="config-grid">
            <span>类型：{{ text(summary(row).base_type) }}</span>
            <span>节数：{{ text(summary(row).stage) }}</span>
            <span>管型：{{ text(summary(row).column_type) }}</span>
            <span>尺寸：{{ text(summary(row).dimensions) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="关键参数" min-width="260">
        <template #default="{ row }">
          <div class="config-grid">
            <span>承重：{{ text(summary(row).load_capacity) }}</span>
            <span>行程：{{ text(summary(row).lifting_range) }}</span>
            <span>速度：{{ text(summary(row).lifting_speed) }}</span>
            <span>包装：{{ text(summary(row).package_size) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="区间报价状态" width="190">
        <template #default="{ row }">
          <el-tag :type="rowStatus(row).type" effect="plain">{{ rowStatus(row).label }}</el-tag>
          <p class="mt-2 text-xs text-slate-500">{{ intervalCount(row) }} 条区间价格</p>
        </template>
      </el-table-column>

      <el-table-column label="颜色/库存参考" width="180">
        <template #default="{ row }">
          <div class="text-sm text-slate-700">{{ text(summary(row).total_available_colors, '0') }} 个颜色选项</div>
          <div class="text-xs text-slate-500">{{ text(summary(row).inventory_reference_count, '0') }} 条库存参考，不承诺库存</div>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :disabled="!row.has_interval_pricing" @click="openIntervalTable(row)">查看区间价</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && !error && !products.length" description="暂无产品。请运行产品导入脚本或调整筛选条件。" />

    <el-drawer v-model="tableDrawer" size="560px" :title="selected ? customerName(selected) : '产品详情'">
      <div v-if="selected" class="drawer-body">
        <img class="drawer-image" :src="productImage(selected)" alt="" />
        <div class="drawer-section">
          <h3>产品配置</h3>
          <dl>
            <dt>Partner</dt><dd>{{ selected.partner_code || selected.partner_name || '未归属' }}</dd>
            <dt>SKU</dt><dd>{{ selected.internal_sku }}</dd>
            <dt>原系统 SKU</dt><dd>{{ selected.partner_product_code || '未维护' }}</dd>
            <dt>产品族</dt><dd>{{ categoryLabel(selected.product_family || selected.product_category) }}</dd>
            <dt>配置来源</dt><dd>{{ text(summary(selected).source_system) }}</dd>
          </dl>
        </div>
        <div class="drawer-section">
          <h3>客户可见区间报价表</h3>
          <el-table v-loading="tableLoading" :data="intervalRows" size="small" border>
            <el-table-column prop="quantity_label" label="Quantity" width="110" />
            <el-table-column label="FOB Unit Price">
              <template #default="{ row }">{{ formatPrice(row.fob_unit_price) }}</template>
            </el-table-column>
            <el-table-column label="DDP Unit Price">
              <template #default="{ row }">{{ formatPrice(row.ddp_unit_price) }}</template>
            </el-table-column>
          </el-table>
          <p v-if="!tableLoading && !intervalRows.length" class="mt-3 text-sm text-amber-700">
            该产品还没有可用区间报价。需要先维护成本模型或 ProductPriceTier。
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
  max-width: 820px;
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
  width: 88px;
  height: 68px;
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

.config-grid {
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
  grid-template-columns: 108px 1fr;
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
</style>
