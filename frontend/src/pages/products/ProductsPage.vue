<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchCatalogProducts, type CatalogProduct } from '@/api/quoteCatalog'

const router = useRouter()
const rows = ref<CatalogProduct[]>([])
const total = ref(0)
const loading = ref(false)
const error = ref('')
const search = ref('')
const partnerCode = ref('')

const partnerOptions = [
  { label: '全部 Partner', value: '' },
  { label: 'HOSUN', value: 'HOSUN' },
  { label: 'JOOBOO', value: 'JOOBOO' },
]

const stats = computed(() => ({
  products: rows.value.length,
  intervalReady: rows.value.filter((row) => row.has_interval_pricing).length,
  withImages: rows.value.filter((row) => row.image_url).length,
  partners: new Set(rows.value.map((row) => row.partner_code || row.partner_name || '未归属')).size,
}))

function imageUrl(row: CatalogProduct) {
  return row.image_url || '/intelliopus-logo.png'
}

function displayName(row: CatalogProduct) {
  return String(row.attributes_json?.['customer_quote_name'] || row.product_name)
}

function summary(row: CatalogProduct) {
  return row.configuration_summary || {}
}

function text(value: unknown, fallback = '未维护') {
  const raw = String(value ?? '').trim()
  return raw || fallback
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchCatalogProducts({
      partner_code: partnerCode.value || undefined,
      search: search.value || undefined,
      limit: 200,
    })
    rows.value = data.items
    total.value = data.total
  } catch (e) {
    error.value = e instanceof Error ? e.message : '产品库加载失败，请确认 backend 已启动并且登录状态有效。'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="product-library">
    <section class="library-header">
      <div>
        <p class="eyebrow">Unified Product Library</p>
        <h1>产品库</h1>
        <p>
          产品库已整合 desk-order-system 的图片、配置、颜色和库存参考，并继续使用 PartnerOS 的成本模型、
          区间报价和客户安全输出规则。HOSUN 与 JOOBOO 作为平级 Partner 维护。
        </p>
      </div>
      <div class="metrics">
        <span><strong>{{ stats.products }}</strong>产品</span>
        <span><strong>{{ stats.intervalReady }}</strong>区间价就绪</span>
        <span><strong>{{ stats.withImages }}</strong>已有图片</span>
        <span><strong>{{ stats.partners }}</strong>Partner</span>
      </div>
    </section>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb-4"
      title="产品图片和库存只作为内部产品目录参考；不会自动承诺库存、认证、交期或发送给客户。"
    />

    <section class="toolbar">
      <el-segmented v-model="partnerCode" :options="partnerOptions" @change="load" />
      <el-input v-model="search" clearable placeholder="搜索 SKU / 产品名称 / 规格" class="w-80" @keyup.enter="load" />
      <el-button type="primary" @click="load">刷新</el-button>
      <el-button @click="router.push('/quote-catalog')">进入报价目录</el-button>
    </section>

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />

    <el-table v-loading="loading" :data="rows" stripe row-key="id">
      <el-table-column label="产品" min-width="390">
        <template #default="{ row }">
          <div class="product-cell">
            <img :src="imageUrl(row)" alt="" />
            <div>
              <div class="title">{{ displayName(row) }}</div>
              <div class="meta">{{ row.internal_sku }} · 原 SKU {{ row.partner_product_code || '未维护' }}</div>
              <div class="mt-2 flex flex-wrap gap-1">
                <el-tag size="small" effect="plain">{{ row.partner_code || row.partner_name || '未归属' }}</el-tag>
                <el-tag v-if="!row.image_url" size="small" type="warning" effect="plain">图片待补</el-tag>
              </div>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="配置" min-width="260">
        <template #default="{ row }">
          <div class="config">
            <span>{{ text(summary(row).base_type) }}</span>
            <span>{{ text(summary(row).stage) }} stage</span>
            <span>{{ text(summary(row).column_type) }}</span>
            <span>{{ text(summary(row).dimensions) }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="关键规格" min-width="260">
        <template #default="{ row }">
          <div class="config muted">
            <span>承重：{{ text(summary(row).load_capacity) }}</span>
            <span>行程：{{ text(summary(row).lifting_range) }}</span>
            <span>速度：{{ text(summary(row).lifting_speed) }}</span>
            <span>包装：{{ text(summary(row).package_size) }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="报价准备" width="180">
        <template #default="{ row }">
          <el-tag :type="row.has_interval_pricing ? 'success' : 'warning'" effect="plain">
            {{ row.has_interval_pricing ? '区间价已维护' : '待维护区间价' }}
          </el-tag>
          <p class="mt-2 text-xs text-slate-500">{{ row.quote_interval_count || 0 }} 条价格区间</p>
        </template>
      </el-table-column>
    </el-table>

    <p class="mt-4 text-sm text-slate-500">
      当前筛选结果 {{ rows.length }} / 总计 {{ total }}。图片缺失的产品不会阻塞内部建档，但不适合直接生成客户报价 PDF。
    </p>
  </div>
</template>

<style scoped>
.library-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
  padding: 22px;
  border: 1px solid #bfdbfe;
  background: #ffffff;
}

.eyebrow {
  margin: 0 0 6px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 720;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 8px;
  color: #0f172a;
  font-size: 26px;
}

.library-header p {
  max-width: 780px;
  margin: 0;
  color: #526174;
  line-height: 1.7;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(100px, 1fr));
  gap: 10px;
  align-self: start;
}

.metrics span {
  padding: 12px;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #64748b;
  text-align: center;
}

.metrics strong {
  display: block;
  color: #1d4ed8;
  font-size: 24px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
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

.title {
  color: #0f172a;
  font-weight: 720;
}

.meta {
  margin-top: 4px;
  color: #64748b;
  font-size: 12px;
}

.config {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.config span {
  padding: 2px 8px;
  border: 1px solid #d8e2ef;
  color: #475569;
  font-size: 12px;
}

.config.muted span {
  background: #f8fafc;
}
</style>
