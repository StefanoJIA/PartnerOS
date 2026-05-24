<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchCatalogProducts, postPricingPreview, type CatalogProduct } from '@/api/quoteCatalog'
import { http } from '@/api/http'

const router = useRouter()
const products = ref<CatalogProduct[]>([])
const productId = ref('')
const quantity = ref(50)
const incoterm = ref('FOB')
const strategy = ref('volume')
const preview = ref<Record<string, unknown> | null>(null)
const loading = ref(false)
const error = ref('')
const billToCompany = ref('')

const SAFETY =
  'Creating a quote records pricing for manual review. intelliOffice does not send quotes automatically.'

async function loadProducts() {
  const data = await fetchCatalogProducts({ limit: 100 })
  products.value = data.items
  if (data.items.length) productId.value = data.items[0].id
}

async function runPreview() {
  if (!productId.value) return
  preview.value = await postPricingPreview({
    product_id: productId.value,
    quantity: quantity.value,
    incoterm: incoterm.value,
    pricing_strategy: strategy.value,
  })
}

async function createQuote() {
  if (!productId.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await http.post('/v1/quotes', {
      line_items: [
        {
          product_id: productId.value,
          quantity: quantity.value,
          incoterm: incoterm.value,
          pricing_strategy: strategy.value,
        },
      ],
      bill_to: { company: billToCompany.value || 'New Customer' },
    })
    if (data.ok && data.data?.id) {
      router.push({ name: 'quote-detail', params: { id: data.data.id } })
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Create quote failed'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await loadProducts()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load products'
  }
})
</script>

<template>
  <div class="page">
    <el-button link @click="router.push({ name: 'quotes' })">← Back to Quotes</el-button>
    <h1>New Quote</h1>
    <el-alert type="warning" :closable="false" show-icon title="Safety" :description="SAFETY" class="mb" />
    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />

    <el-form label-width="140px" class="form">
      <el-form-item label="Bill To Company">
        <el-input v-model="billToCompany" placeholder="Customer company name" />
      </el-form-item>
      <el-form-item label="Product">
        <el-select v-model="productId" filterable style="width: 100%">
          <el-option v-for="p in products" :key="p.id" :label="p.product_name" :value="p.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="Quantity">
        <el-input-number v-model="quantity" :min="1" />
      </el-form-item>
      <el-form-item label="Incoterm">
        <el-select v-model="incoterm"><el-option label="FOB" value="FOB" /><el-option label="DDP" value="DDP" /></el-select>
      </el-form-item>
      <el-form-item label="Strategy">
        <el-select v-model="strategy">
          <el-option label="Volume" value="volume" />
          <el-option label="Traffic" value="traffic" />
          <el-option label="Profit" value="profit" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button @click="runPreview">Preview Price</el-button>
        <el-button type="primary" :loading="loading" @click="createQuote">Create Quote</el-button>
      </el-form-item>
    </el-form>

    <el-card v-if="preview" shadow="never" class="mb">
      <template #header>Price Preview</template>
      <p>Source: {{ preview.source }}</p>
      <p v-if="preview.price_breakdown">Unit: {{ (preview.price_breakdown as Record<string,string>).final_unit_price_after_discount }}</p>
    </el-card>
  </div>
</template>

<style scoped>
.page { padding: 16px; }
.mb { margin-bottom: 16px; }
.form { max-width: 560px; }
</style>
