<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchCatalogProducts, type CatalogProduct } from '@/api/quoteCatalog'

const router = useRouter()
const rows = ref<CatalogProduct[]>([])
const total = ref(0)
const loading = ref(false)
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
  partners: new Set(rows.value.map((row) => row.partner_code || row.partner_name || '未归属')).size,
}))

function imageUrl(row: CatalogProduct) {
  return row.image_url || '/favicon.svg'
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
  try {
    const data = await fetchCatalogProducts({
      partner_code: partnerCode.value || undefined,
      search: search.value || undefined,
      limit: 200,
    })
    rows.value = data.items
    total.value = data.total
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
        <p>产品库已与报价目录合并：目录、配置、图片、颜色/库存参考和区间报价状态使用同一套 PartnerOS ProductCatalog。</p>
      </div>
      <div class="metrics">
        <span><strong>{{ stats.products }}</strong>产品</span>
        <span><strong>{{ stats.intervalReady }}</strong>区间价就绪</span>
        <span><strong>{{ stats.partners }}</strong>Partner</span>
      </div>
    </section>

    <section class="toolbar">
      <el-segmented v-model="partnerCode" :options="partnerOptions" @change="load" />
      <el-input v-model="search" clearable placeholder="搜索 SKU / 产品名称" class="w-72" @keyup.enter="load" />
      <el-button type="primary" @click="load">刷新</el-button>
      <el-button @click="router.push('/quote-catalog')">进入报价目录</el-button>
    </section>

    <el-table v-loading="loading" :data="rows" stripe row-key="id">
      <el-table-column label="产品" min-width="360">
        <template #default="{ row }">
          <div class="product-cell">
            <img :src="imageUrl(row)" alt="" />
            <div>
              <div class="title">{{ displayName(row) }}</div>
              <div class="meta">{{ row.internal_sku }} · {{ row.partner_product_code || '无原始 SKU' }}</div>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="Partner" width="150">
        <template #default="{ row }">
          <el-tag effect="plain">{{ row.partner_code || row.partner_name || '未归属' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="配置" min-width="240">
        <template #default="{ row }">
          <div class="config">
            <span>{{ text(summary(row).base_type) }}</span>
            <span>{{ text(summary(row).stage) }} stage</span>
            <span>{{ text(summary(row).column_type) }}</span>
            <span>{{ text(summary(row).dimensions) }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="报价准备" width="170">
        <template #default="{ row }">
          <el-tag :type="row.has_interval_pricing ? 'success' : 'warning'" effect="plain">
            {{ row.has_interval_pricing ? '区间价已维护' : '待维护区间价' }}
          </el-tag>
          <p class="mt-2 text-xs text-slate-500">{{ row.quote_interval_count || 0 }} 条</p>
        </template>
      </el-table-column>
    </el-table>

    <p class="mt-4 text-sm text-slate-500">当前筛选结果 {{ rows.length }} / 总计 {{ total }}。库存只作内部参考，不自动承诺。</p>
  </div>
</template>

<style scoped>
.library-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
  padding: 22px;
  border: 1px solid #d8e2ef;
  background: #fff;
}

.eyebrow {
  margin: 0 0 6px;
  color: #0f6b78;
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
  margin: 0;
  color: #526174;
}

.metrics {
  display: flex;
  gap: 10px;
  align-self: start;
}

.metrics span {
  min-width: 98px;
  padding: 12px;
  border: 1px solid #d8e2ef;
  background: #f8fafc;
  color: #64748b;
  text-align: center;
}

.metrics strong {
  display: block;
  color: #0f6b78;
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
  width: 84px;
  height: 64px;
  object-fit: contain;
  border: 1px solid #e2e8f0;
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
</style>
