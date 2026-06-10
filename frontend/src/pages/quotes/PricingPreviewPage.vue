<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchCatalogProducts, postPricingPreview, type CatalogProduct, type PricingPreviewResult } from '@/api/quoteCatalog'

const SAFETY =
  '价格预览只用于内部测算，不会创建报价、发送消息，也不会承诺库存、认证或交期。'

const loading = ref(false)
const products = ref<CatalogProduct[]>([])
const productId = ref('')
const quantity = ref(100)
const incoterm = ref('FOB')
const strategy = ref('volume')
const discountPct = ref<number | null>(null)
const result = ref<PricingPreviewResult | null>(null)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const data = await fetchCatalogProducts()
    products.value = data.items
    if (data.items.length) productId.value = data.items[0].id
  } catch {
    error.value = '产品加载失败。'
  }
})

async function preview() {
  if (!productId.value) return
  loading.value = true
  error.value = null
  result.value = null
  try {
    result.value = await postPricingPreview({
      product_id: productId.value,
      quantity: quantity.value,
      incoterm: incoterm.value,
      pricing_strategy: strategy.value,
      discount: discountPct.value ? { type: 'percentage', value: discountPct.value } : undefined,
    })
  } catch {
    error.value = '价格预览失败，请检查 backend、汇率和价格阶梯。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h2 class="mb-4 text-lg font-semibold text-slate-800">价格预览</h2>
    <el-alert type="info" :closable="false" show-icon class="mb-4" :title="SAFETY" />
    <el-form label-width="140px" class="max-w-xl">
      <el-form-item label="产品">
        <el-select v-model="productId" filterable style="width: 100%">
          <el-option v-for="p in products" :key="p.id" :label="`${p.internal_sku} — ${p.product_name}`" :value="p.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="数量">
        <el-input-number v-model="quantity" :min="1" />
      </el-form-item>
      <el-form-item label="Incoterm">
        <el-select v-model="incoterm">
          <el-option label="FOB" value="FOB" />
          <el-option label="DDP" value="DDP" />
          <el-option label="EXW" value="EXW" />
          <el-option label="CIF" value="CIF" />
        </el-select>
      </el-form-item>
      <el-form-item label="策略">
        <el-select v-model="strategy">
          <el-option label="Volume 销量" value="volume" />
          <el-option label="Traffic 引流" value="traffic" />
          <el-option label="Profit 利润" value="profit" />
        </el-select>
      </el-form-item>
      <el-form-item label="折扣 %">
        <el-input-number v-model="discountPct" :min="0" :max="100" :precision="1" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="preview">预览</el-button>
      </el-form-item>
    </el-form>
    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb-3" :title="error" />
    <el-card v-if="result" shadow="never">
      <p class="mb-2 text-sm"><strong>来源：</strong>{{ result.source }}</p>
      <p class="mb-2 text-sm"><strong>行项目小计：</strong>{{ result.price_breakdown?.line_subtotal }} {{ result.currency }}</p>
      <p class="mb-2 text-sm"><strong>预估毛利：</strong>{{ result.profit_breakdown?.estimated_margin }}%</p>
      <el-alert v-for="(w, i) in result.warnings" :key="i" type="warning" :closable="false" show-icon class="mb-2" :title="w" />
      <p class="text-xs text-slate-500">quote_created={{ result.safety.quote_created }}</p>
    </el-card>
  </div>
</template>
