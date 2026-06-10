<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchCatalogProducts, type CatalogProduct } from '@/api/quoteCatalog'

const loading = ref(false)
const error = ref<string | null>(null)
const products = ref<CatalogProduct[]>([])
const category = ref('')
const search = ref('')

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await fetchCatalogProducts({
      category: category.value || undefined,
      search: search.value || undefined,
    })
    products.value = data.items
  } catch {
    error.value = '报价目录加载失败，请检查 backend 和登录状态。'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h2 class="mb-4 text-lg font-semibold text-slate-800">报价产品目录</h2>
    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb-4"
      title="报价目录只用于样品/演示价格预览，不会自动创建报价。"
    />
    <div class="mb-4 flex flex-wrap gap-2">
      <el-input v-model="search" placeholder="搜索 SKU 或名称" clearable style="width: 220px" @keyup.enter="load" />
      <el-input v-model="category" placeholder="分类筛选" clearable style="width: 180px" @keyup.enter="load" />
      <el-button type="primary" @click="load">刷新</el-button>
    </div>
    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />
    <el-table v-loading="loading" :data="products" stripe>
      <el-table-column prop="internal_sku" label="SKU" width="160" />
      <el-table-column prop="product_name" label="产品" min-width="200" />
      <el-table-column prop="product_category" label="分类" width="140" />
      <el-table-column prop="status" label="状态" width="90" />
      <el-table-column label="属性" min-width="180">
        <template #default="{ row }">
          <span class="text-xs text-slate-600">{{ JSON.stringify(row.attributes_json || {}) }}</span>
        </template>
      </el-table-column>
    </el-table>
    <p v-if="!loading && !error && !products.length" class="mt-4 text-sm text-slate-500">
      暂无报价目录产品，请在 backend 运行 seed_quote_catalog.py。
    </p>
  </div>
</template>
