<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createCatalogProduct,
  deleteCatalogProduct,
  fetchCatalogProducts,
  fetchProductPartnerOptions,
  fetchPricingAssumptions,
  postPricingPreview,
  updateCatalogProduct,
  updateOceanFreightAssumption,
  type CatalogProduct,
  type IntervalQuoteRow,
  type ProductPartnerOption,
  type PricingAssumptionSnapshot,
} from '@/api/quoteCatalog'

interface ProductForm {
  partner_id: string
  internal_sku: string
  partner_product_code: string
  product_name: string
  product_category: string
  product_family: string
  description_customer: string
  description_internal: string
  image_url: string
  status: string
}

const loading = ref(false)
const tableLoading = ref(false)
const savingMargin = ref(false)
const error = ref<string | null>(null)
const router = useRouter()
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
const productPartnerOptions = ref<ProductPartnerOption[]>([])
const productDialog = ref(false)
const productSaving = ref(false)
const editingProduct = ref<CatalogProduct | null>(null)
const productForm = ref<ProductForm>(defaultProductForm())

const QUANTITY_RANGES = [
  { min_qty: 1, max_qty: 49, quantity_label: '1-49', concession: 1, fobAvailable: false },
  { min_qty: 50, max_qty: 99, quantity_label: '50-99', concession: 0.97, fobAvailable: true },
  { min_qty: 100, max_qty: 299, quantity_label: '100-299', concession: 0.94, fobAvailable: true },
  { min_qty: 300, max_qty: 499, quantity_label: '300-499', concession: 0.92, fobAvailable: true },
  { min_qty: 500, max_qty: null, quantity_label: '>=500', concession: 0.9, fobAvailable: true },
]

const partnerOptions = [
  { label: '全部 Partner', value: '' },
  { label: 'HOSUN', value: 'HOSUN' },
  { label: 'JOOBOO', value: 'JOOBOO' },
]

const categoryOptions = computed(() =>
  Array.from(new Set(products.value.map((item) => item.product_family || item.product_category).filter(Boolean))).sort(),
)

const partnerStats = computed(() => {
  const base = new Map<string, number>()
  for (const product of products.value) {
    const key = product.partner_code || product.partner_name || '未归属'
    base.set(key, (base.get(key) || 0) + 1)
  }
  return Array.from(base.entries()).map(([partner, count]) => ({ partner, count }))
})

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

function summary(product: CatalogProduct) {
  return product.configuration_summary || {}
}

function pricing(product: CatalogProduct | null) {
  return product?.pricing_model_summary || {}
}

function display(value: unknown, fallback = '待维护') {
  const raw = String(value ?? '').trim()
  return raw || fallback
}

function money(value: unknown, prefix = '$') {
  if (value === null || value === undefined || value === '') return '待维护'
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return String(value)
  return `${prefix}${numeric.toFixed(2)}`
}

function numberText(value: unknown, suffix = '') {
  if (value === null || value === undefined || value === '') return '待维护'
  const numeric = Number(value)
  return Number.isFinite(numeric) ? `${numeric.toFixed(2)}${suffix}` : `${value}${suffix}`
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
    general_product_family: '通用产品',
    product_catalog: '产品目录',
  }
  return value ? labels[value] || value : '未分类'
}

function partnerLabel(product: CatalogProduct) {
  return product.partner_code || product.partner_name || '未归属'
}

function productImage(product: CatalogProduct) {
  return product.image_url || '/intelliopus-logo.png'
}

function customerName(product: CatalogProduct) {
  const attrs = product.attributes_json || {}
  return String(attrs.customer_quote_name || product.product_name)
}

function displaySku(product: CatalogProduct) {
  const source = product.partner_product_code || product.internal_sku || ''
  return source.replace(/^IO-[A-Z]+-[A-Z]+-/, '')
}

function marginValue(product: CatalogProduct | null) {
  const value = pricing(product).product_target_margin_percent
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

function formatPrice(value: string | null | undefined) {
  if (!value || value === 'N/A') return 'N/A'
  const numeric = Number(value)
  return Number.isFinite(numeric) ? `$${numeric.toFixed(2)}` : value
}

function numericFromPricing(value: unknown) {
  if (value === null || value === undefined || value === '') return null
  const numeric = Number(String(value).replace(/[$,]/g, ''))
  return Number.isFinite(numeric) ? numeric : null
}

function recalculateIntervalRowsFromDraft() {
  if (!selected.value) return false
  const margin = Number(marginPercentDraft.value)
  if (!Number.isFinite(margin) || margin < 0) return false
  const summary = pricing(selected.value)
  const fobCost = numericFromPricing(summary.fob_cost_usd)
  const ddpCost = numericFromPricing(summary.ddp_cost_usd)
  if (ddpCost === null) return false
  const productMultiplier = 1 + margin / 100
  intervalRows.value = QUANTITY_RANGES.map((range) => {
    const multiplier = productMultiplier * range.concession
    const fobUnitPrice = range.fobAvailable && fobCost !== null ? (fobCost * multiplier).toFixed(2) : null
    const ddpUnitPrice = (ddpCost * multiplier).toFixed(2)
    return {
      min_qty: range.min_qty,
      max_qty: range.max_qty,
      quantity_label: range.quantity_label,
      currency: 'USD',
      fob_unit_price: fobUnitPrice,
      ddp_unit_price: ddpUnitPrice,
      incoterms_available: range.fobAvailable ? ['FOB', 'DDP'] : ['DDP'],
      customer_visible: true,
      pricing_basis: 'live_cost_margin_preview',
    } as IntervalQuoteRow
  })
  return true
}

function rowStatus(product: CatalogProduct) {
  if (product.has_interval_pricing) return { label: '区间报价已维护', type: 'success' as const }
  return { label: '缺少区间报价', type: 'warning' as const }
}

function catalogRowStyle() {
  return { height: '116px' }
}

function defaultProductForm(): ProductForm {
  return {
    partner_id: '',
    internal_sku: '',
    partner_product_code: '',
    product_name: '',
    product_category: 'lifting_systems',
    product_family: 'desk_frames',
    description_customer: '',
    description_internal: '',
    image_url: '',
    status: 'active',
  }
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

async function loadPartnerOptions() {
  try {
    const data = await fetchProductPartnerOptions()
    productPartnerOptions.value = data.items
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : 'Partner 选项加载失败')
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

function openCreateProduct() {
  const preferred =
    productPartnerOptions.value.find((item) => item.partner_code === partnerCode.value)
    || productPartnerOptions.value[0]
  editingProduct.value = null
  productForm.value = { ...defaultProductForm(), partner_id: preferred?.id || '' }
  productDialog.value = true
}

function openEditProduct(product: CatalogProduct) {
  editingProduct.value = product
  productForm.value = {
    partner_id: product.partner_id,
    internal_sku: product.internal_sku || '',
    partner_product_code: product.partner_product_code || '',
    product_name: product.product_name || '',
    product_category: product.product_category || 'lifting_systems',
    product_family: product.product_family || '',
    description_customer: product.description_customer || '',
    description_internal: String(product.attributes_json?.description_internal || ''),
    image_url: product.image_url || '',
    status: product.status || 'active',
  }
  productDialog.value = true
}

async function saveProductForm() {
  const form = productForm.value
  if (!form.product_name.trim() || !form.internal_sku.trim()) {
    ElMessage.error('产品名称和产品编号必须填写')
    return
  }
  if (!editingProduct.value && !form.partner_id) {
    ElMessage.error('请选择 Partner')
    return
  }
  productSaving.value = true
  try {
    const payload = {
      internal_sku: form.internal_sku.trim(),
      partner_product_code: form.partner_product_code.trim() || null,
      product_name: form.product_name.trim(),
      product_category: form.product_category.trim() || 'lifting_systems',
      product_family: form.product_family.trim() || null,
      description_customer: form.description_customer.trim() || null,
      description_internal: form.description_internal.trim() || null,
      status: form.status || 'active',
      default_uom: 'EA',
      base_currency: 'USD',
      default_incoterm: 'FOB',
      image_url: form.image_url.trim() || null,
      attributes_json: editingProduct.value?.attributes_json || {
        source_system: 'manual_catalog_entry',
        customer_safe_pricing_mode: 'full_quantity_interval_quote_table',
      },
    }
    if (editingProduct.value) {
      await updateCatalogProduct(editingProduct.value.id, payload)
      ElMessage.success('产品资料已更新')
    } else {
      await createCatalogProduct({
        ...payload,
        partner_id: form.partner_id,
      })
      ElMessage.success('产品已新增')
    }
    productDialog.value = false
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '产品保存失败')
  } finally {
    productSaving.value = false
  }
}

async function deleteProduct(row: CatalogProduct) {
  try {
    await ElMessageBox.confirm(
      `确认从报价目录移除「${customerName(row)}」？该操作会将产品状态改为 inactive，不会删除历史报价和成本记录。`,
      '删除产品',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await deleteCatalogProduct(row.id)
    ElMessage.success('产品已从当前目录移除')
    if (selected.value?.id === row.id) {
      tableDrawer.value = false
      selected.value = null
    }
    await load()
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '产品删除失败')
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
      notes: 'Updated from quote catalog assumptions panel.',
    })
    ElMessage.success('海运单价已保存，目录成本将按最新假设重新计算。')
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
    recalculateIntervalRowsFromDraft()
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
    ElMessage.success('产品利润率已保存，区间报价已按当前计价模型重新计算。')
    await load()
    const refreshed = products.value.find((item) => item.id === selected.value?.id)
    if (refreshed) selected.value = refreshed
    if (selected.value) {
      await openIntervalTable(selected.value)
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
  loadPartnerOptions()
  loadAssumptions()
  load()
})

watch(marginPercentDraft, () => {
  if (!tableDrawer.value || tableLoading.value) return
  recalculateIntervalRowsFromDraft()
})
</script>

<template>
  <div class="catalog-page">
    <section class="catalog-hero">
      <div>
        <p class="eyebrow">Quote Catalog / Internal Pricing Source</p>
        <h1>报价产品目录</h1>
        <p class="hero-copy">
          这里维护报价选品、规格、区间价格和内部计价模型。客户报价单只展示英文产品名和完整数量区间单价；成本、利润、汇率和海运只在内部可见。
        </p>
      </div>
      <div class="hero-metrics">
        <el-button type="primary" @click="router.push('/admin/quotes/new')">新建报价单</el-button>
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
      title="安全边界：报价目录不会自动创建报价、不会发送邮件、不会通知客户、不会承诺库存或交期。"
    />

    <section class="assumption-panel">
      <div>
        <p class="eyebrow">Pricing Assumptions</p>
        <h2>汇率与海运单价</h2>
        <p>
          产品固定人民币出厂成本和重量来自产品成本模型；海运单价独立维护，当前先按供应商报价 22 RMB/kg 计算；USD/CNY 使用后端实时汇率服务更新。
          后续如拿到整柜或批量海运阶梯，可在这里升级为按数量/柜型的独立运费表。
        </p>
      </div>
      <div class="assumption-cards">
        <div class="assumption-card">
          <span>海运单价</span>
          <strong>
            {{
              assumptions
                ? numberText(assumptions.ocean_freight.numeric_value, ` ${assumptions.ocean_freight.unit || 'RMB/kg'}`)
                : '22.00 RMB/kg'
            }}
          </strong>
          <small>来源：{{ assumptions?.ocean_freight.source || 'manual_provider_quote' }}</small>
          <div class="assumption-edit">
            <el-input-number v-model="oceanFreightDraft" :min="0.01" :precision="2" :step="1" :disabled="assumptionLoading" />
            <el-button type="primary" :loading="assumptionSaving" @click="saveOceanFreightAssumption">保存</el-button>
          </div>
        </div>
        <div class="assumption-card">
          <span>实时汇率 USD/CNY</span>
          <strong>{{ fxSummary ? numberText(fxSummary.rate) : '待加载' }}</strong>
          <small>{{ fxSummary ? `${fxSummary.date || '无日期'} / ${fxSummary.source || 'unknown'}` : '来自后端最新汇率记录' }}</small>
          <el-tag v-if="fxSummary?.stale" type="warning" effect="plain">汇率可能过期</el-tag>
        </div>
        <div class="assumption-card">
          <span>利润额度表</span>
          <strong>引流 / 销量 / 利润</strong>
          <small>每个数量区间独立倍率：1-49、50-99、100-299、300-499、500+。</small>
        </div>
      </div>
    </section>

    <section class="toolbar">
      <el-segmented v-model="partnerCode" :options="partnerOptions" @change="load" />
      <el-select v-model="category" clearable placeholder="分类筛选" class="w-56" @change="load">
        <el-option v-for="item in categoryOptions" :key="item" :label="categoryLabel(item)" :value="item" />
      </el-select>
      <el-input v-model="search" clearable placeholder="搜索 SKU / 产品名 / 原厂型号" class="w-80" @keyup.enter="load" />
      <el-button type="primary" @click="load">刷新</el-button>
      <el-button @click="clearFilters">清空</el-button>
      <el-button type="success" @click="openCreateProduct">新增产品</el-button>
    </section>

    <div class="partner-strip">
      <el-tag v-for="item in partnerStats" :key="item.partner" effect="plain">
        {{ item.partner }} · {{ item.count }} 个产品
      </el-tag>
      <el-tag type="success" effect="plain">HOSUN / JOOBOO 平级 Partner</el-tag>
    </div>

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />

    <el-table v-loading="loading" :data="products" stripe class="catalog-table" row-key="id" :row-style="catalogRowStyle">
      <el-table-column label="产品" min-width="420">
        <template #default="{ row }">
          <div class="product-cell">
            <div class="product-image-frame">
              <img :src="productImage(row)" alt="" />
            </div>
            <div class="product-copy">
              <div class="product-title">{{ customerName(row) }}</div>
              <div class="product-meta">
                产品编号 {{ displaySku(row) }}
              </div>
              <div class="tag-row">
                <el-tag size="small" effect="plain">{{ partnerLabel(row) }}</el-tag>
                <el-tag size="small" type="info" effect="plain">{{ categoryLabel(row.product_family || row.product_category) }}</el-tag>
                <el-tag v-if="!row.image_url" size="small" type="warning" effect="plain">图片待补</el-tag>
              </div>
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="规格参数" min-width="320">
        <template #default="{ row }">
          <div class="config-grid">
            <span>类型：{{ display(summary(row).base_type) }}</span>
            <span>节数：{{ display(summary(row).stage) }}</span>
            <span>尺寸：{{ display(summary(row).dimensions) }}</span>
            <span>承重：{{ display(summary(row).load_capacity) }}</span>
            <span v-if="summary(row).total_estimated_load_capacity" class="muted">
              总承重参考：{{ summary(row).total_estimated_load_capacity }}
            </span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="内部计价模型" min-width="300">
        <template #default="{ row }">
          <div class="pricing-grid">
            <span>出厂成本：{{ money(pricing(row).factory_cost_rmb, '¥') }}</span>
            <span>重量：{{ numberText(pricing(row).unit_weight_kg, ' kg') }}</span>
            <span>FOB 成本：{{ money(pricing(row).fob_cost_usd) }}</span>
            <span>DDP 成本：{{ money(pricing(row).ddp_cost_usd) }}</span>
            <span>目标利润率：{{ numberText(pricing(row).product_target_margin_percent, '%') }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="区间报价" width="180">
        <template #default="{ row }">
          <el-tag :type="rowStatus(row).type" effect="plain">{{ rowStatus(row).label }}</el-tag>
          <p class="small-note">{{ Number(row.quote_interval_count || 0) }} 条区间价格</p>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <div class="row-actions">
            <el-button size="small" @click="openIntervalTable(row)">计价模型</el-button>
            <el-button size="small" @click="openEditProduct(row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="deleteProduct(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && !error && !products.length" description="暂无产品，请先导入目录或调整筛选条件。" />

    <el-dialog v-model="productDialog" :title="editingProduct ? '编辑产品' : '新增产品'" width="720px">
      <el-form label-width="110px" class="product-form">
        <el-form-item label="Partner">
          <el-select v-model="productForm.partner_id" placeholder="选择 Partner" :disabled="Boolean(editingProduct)">
            <el-option
              v-for="item in productPartnerOptions"
              :key="item.id"
              :label="`${item.partner_code || 'NO-CODE'} · ${item.partner_name}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="产品编号">
          <el-input v-model="productForm.internal_sku" placeholder="例如 HS11A 或 HS90602PRLCZ" />
        </el-form-item>
        <el-form-item label="原厂型号">
          <el-input v-model="productForm.partner_product_code" placeholder="可与产品编号一致" />
        </el-form-item>
        <el-form-item label="英文产品名">
          <el-input v-model="productForm.product_name" placeholder="客户报价使用英文产品名" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="productForm.product_family" filterable allow-create default-first-option placeholder="产品线">
            <el-option label="桌架" value="desk_frames" />
            <el-option label="升降柱" value="lifting_columns" />
            <el-option label="多人位桌架" value="benching_frames" />
            <el-option label="重载升降系统" value="heavy_duty_supply" />
            <el-option label="配件" value="desk_accessories" />
            <el-option label="气动升降桌" value="pneumatic_standing_desks" />
            <el-option label="教育家具" value="education_furniture" />
            <el-option label="项目制家具" value="project_furniture" />
          </el-select>
        </el-form-item>
        <el-form-item label="产品大类">
          <el-input v-model="productForm.product_category" placeholder="默认 lifting_systems" />
        </el-form-item>
        <el-form-item label="图片路径">
          <el-input v-model="productForm.image_url" placeholder="/desk-order-assets/products/..." />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="productForm.status">
            <el-radio-button label="active">启用</el-radio-button>
            <el-radio-button label="inactive">停用</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="客户描述">
          <el-input v-model="productForm.description_customer" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="内部备注">
          <el-input v-model="productForm.description_internal" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="productDialog = false">取消</el-button>
        <el-button type="primary" :loading="productSaving" @click="saveProductForm">保存产品</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="tableDrawer" size="720px" :title="selected ? customerName(selected) : '产品详情'">
      <div v-if="selected" class="drawer-body">
        <img class="drawer-image" :src="productImage(selected)" alt="" />

        <section class="drawer-section">
          <h3>产品与规格</h3>
          <dl>
            <dt>Partner</dt><dd>{{ partnerLabel(selected) }}</dd>
            <dt>产品编号</dt><dd>{{ displaySku(selected) }}</dd>
            <dt>原厂型号</dt><dd>{{ selected.partner_product_code || display(summary(selected).partner_model) }}</dd>
            <dt>产品线</dt><dd>{{ categoryLabel(selected.product_family || selected.product_category) }}</dd>
            <dt>承重</dt><dd>{{ display(summary(selected).load_capacity) }}</dd>
          </dl>
          <p v-if="summary(selected).load_capacity_note" class="model-note">{{ summary(selected).load_capacity_note }}</p>
        </section>

        <section class="drawer-section">
          <h3>内部计价参数</h3>
          <dl>
            <dt>人民币出厂成本</dt><dd>{{ money(pricing(selected).factory_cost_rmb, '¥') }}</dd>
            <dt>单位重量</dt><dd>{{ numberText(pricing(selected).unit_weight_kg, ' kg') }}</dd>
            <dt>海运单价</dt><dd>{{ numberText(pricing(selected).ocean_freight_unit_price, ` ${pricing(selected).ocean_freight_unit || 'RMB/kg'}`) }}</dd>
            <dt>实时汇率</dt><dd>{{ numberText(pricing(selected).fx_rate_usd_cny) }} · {{ display(pricing(selected).fx_rate_date) }}</dd>
            <dt>FOB / DDP 成本</dt><dd>{{ money(pricing(selected).fob_cost_usd) }} / {{ money(pricing(selected).ddp_cost_usd) }}</dd>
            <dt>产品利润率</dt>
            <dd class="margin-edit">
              <el-input-number v-model="marginPercentDraft" :min="0" :max="300" :precision="2" />
              <span>%</span>
              <el-button size="small" type="primary" :loading="savingMargin" @click="saveMargin">保存利润率</el-button>
            </dd>
          </dl>
          <p class="model-note">
            区间报价按当前模型实时计算：人民币出厂成本、单位重量、海运单价、实时汇率和产品利润率共同决定 FOB / DDP 单价；数量越大按区间递减倍率让利。
            客户可见报价仍只输出 Quantity、FOB Unit Price、DDP Unit Price。
          </p>
        </section>

        <section class="drawer-section">
          <h3>客户可见区间报价表</h3>
          <el-table v-loading="tableLoading" :data="intervalRows" size="small" border>
            <el-table-column prop="quantity_label" label="Quantity" width="130" />
            <el-table-column label="FOB Unit Price">
              <template #default="{ row }">{{ formatPrice(row.fob_unit_price) }}</template>
            </el-table-column>
            <el-table-column label="DDP Unit Price">
              <template #default="{ row }">{{ formatPrice(row.ddp_unit_price) }}</template>
            </el-table-column>
          </el-table>
          <p v-if="!tableLoading && !intervalRows.length" class="empty-inline">
            该产品还没有可用区间报价，请先维护成本模型或 ProductPriceTier。
          </p>
        </section>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.catalog-page {
  color: #172033;
}

.catalog-hero,
.assumption-panel {
  border: 1px solid #c6d8f0;
  background: #fff;
}

.catalog-hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 18px;
  padding: 22px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #2f5f9f;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}

.catalog-hero h1,
.assumption-panel h2 {
  margin: 0;
  color: #111827;
}

.catalog-hero h1 {
  font-size: 26px;
  font-weight: 760;
}

.hero-copy,
.assumption-panel p {
  margin: 10px 0 0;
  color: #556477;
  line-height: 1.7;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(92px, 1fr));
  gap: 10px;
  align-self: start;
}

.hero-metrics div,
.assumption-card {
  border: 1px solid #d5e3f5;
  background: #f7fbff;
}

.hero-metrics div {
  min-width: 92px;
  padding: 12px;
  text-align: center;
}

.hero-metrics span,
.assumption-card strong {
  display: block;
  color: #2f5f9f;
  font-weight: 760;
}

.hero-metrics span {
  font-size: 24px;
}

.hero-metrics small,
.assumption-card small,
.muted,
.small-note,
.model-note {
  color: #64748b;
}

.assumption-panel {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(520px, 1.5fr);
  gap: 18px;
  margin-bottom: 16px;
  padding: 18px;
}

.assumption-panel h2 {
  font-size: 20px;
  font-weight: 740;
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
  min-height: 128px;
  padding: 12px;
}

.assumption-card span {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.assumption-card strong {
  font-size: 22px;
  line-height: 1.15;
}

.assumption-edit,
.toolbar,
.partner-strip,
.tag-row,
.margin-edit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar,
.partner-strip {
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.tag-row {
  flex-wrap: wrap;
  margin-top: 8px;
}

.product-cell {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  align-items: center;
  gap: 14px;
  min-height: 96px;
}

.product-image-frame {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 112px;
  height: 84px;
  padding: 6px;
  border: 1px solid #d5e3f5;
  background: #fff;
}

.product-image-frame img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.product-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  min-height: 84px;
}

.product-title {
  color: #111827;
  font-weight: 720;
  line-height: 1.35;
}

.product-meta,
.small-note {
  margin-top: 4px;
  font-size: 12px;
}

.config-grid,
.pricing-grid {
  display: grid;
  gap: 4px;
  color: #475569;
  font-size: 13px;
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.row-actions .el-button + .el-button {
  margin-left: 0;
}

.product-form :deep(.el-select),
.product-form :deep(.el-input),
.product-form :deep(.el-textarea) {
  width: 100%;
}

.catalog-table :deep(.el-table__cell) {
  vertical-align: middle;
}

.drawer-body {
  display: grid;
  gap: 18px;
}

.drawer-image {
  width: 100%;
  height: 260px;
  object-fit: contain;
  border: 1px solid #d5e3f5;
  background: #fff;
}

.drawer-section {
  border-top: 1px solid #e2e8f0;
  padding-top: 14px;
}

.drawer-section h3 {
  margin: 0 0 10px;
  color: #111827;
  font-size: 16px;
  font-weight: 720;
}

dl {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 8px 12px;
  margin: 0;
  font-size: 14px;
}

dt {
  color: #64748b;
}

dd {
  margin: 0;
  color: #111827;
}

.model-note,
.empty-inline {
  font-size: 12px;
  line-height: 1.6;
}

.empty-inline {
  margin-top: 10px;
  color: #9a6700;
}
</style>
