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
    error.value = 'Could not load quote catalog. Check backend and login.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h2 class="mb-4 text-lg font-semibold text-slate-800">Quote Product Catalog</h2>
    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb-4"
      title="D6.2 catalog foundation — sample/demo pricing only. Does not create quotes."
    />
    <div class="mb-4 flex flex-wrap gap-2">
      <el-input v-model="search" placeholder="Search SKU or name" clearable style="width: 220px" @keyup.enter="load" />
      <el-input v-model="category" placeholder="Category filter" clearable style="width: 180px" @keyup.enter="load" />
      <el-button type="primary" @click="load">Refresh</el-button>
    </div>
    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />
    <el-table v-loading="loading" :data="products" stripe>
      <el-table-column prop="internal_sku" label="SKU" width="160" />
      <el-table-column prop="product_name" label="Product" min-width="200" />
      <el-table-column prop="product_category" label="Category" width="140" />
      <el-table-column prop="status" label="Status" width="90" />
      <el-table-column label="Attributes" min-width="180">
        <template #default="{ row }">
          <span class="text-xs text-slate-600">{{ JSON.stringify(row.attributes_json || {}) }}</span>
        </template>
      </el-table-column>
    </el-table>
    <p v-if="!loading && !error && !products.length" class="mt-4 text-sm text-slate-500">
      No catalog products. Run seed_quote_catalog.py on the backend.
    </p>
  </div>
</template>
