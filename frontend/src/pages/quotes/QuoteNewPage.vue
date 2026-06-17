<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchCatalogProducts, postPricingPreview, type CatalogProduct, type PricingPreviewResult } from '@/api/quoteCatalog'
import { http } from '@/api/http'

const router = useRouter()
const products = ref<CatalogProduct[]>([])
const productId = ref('')
const quantity = ref(50)
const incoterm = ref('FOB')
const strategy = ref('volume')
const preview = ref<PricingPreviewResult | null>(null)
const loading = ref(false)
const error = ref('')
const billToCompany = ref('')

const SAFETY =
  '创建报价只会保存内部报价记录和报价模型快照，不会自动发送邮件、不会通知客户、不会承诺库存、认证或交期。成本、利润和物流测算保持内部可见。'

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
    error.value = e instanceof Error ? e.message : '创建报价失败'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await loadProducts()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '产品加载失败'
  }
})
</script>

<template>
  <div class="page">
    <el-button link @click="router.push({ name: 'quotes' })">返回报价列表</el-button>
    <h1>新建报价</h1>
    <el-alert type="warning" :closable="false" show-icon title="安全边界" :description="SAFETY" class="mb" />
    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />

    <el-form label-width="120px" class="form">
      <el-form-item label="客户公司">
        <el-input v-model="billToCompany" placeholder="客户公司名称" />
      </el-form-item>
      <el-form-item label="产品">
        <el-select v-model="productId" filterable style="width: 100%">
          <el-option v-for="p in products" :key="p.id" :label="p.product_name" :value="p.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="数量">
        <el-input-number v-model="quantity" :min="1" />
      </el-form-item>
      <el-form-item label="贸易条款">
        <el-select v-model="incoterm">
          <el-option label="FOB" value="FOB" />
          <el-option label="DDP" value="DDP" />
        </el-select>
      </el-form-item>
      <el-form-item label="报价策略">
        <el-select v-model="strategy">
          <el-option label="销量" value="volume" />
          <el-option label="引流" value="traffic" />
          <el-option label="利润" value="profit" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button @click="runPreview">预览价格</el-button>
        <el-button type="primary" :loading="loading" @click="createQuote">创建报价</el-button>
      </el-form-item>
    </el-form>

    <el-card v-if="preview" shadow="never" class="mb">
      <template #header>报价模型预览</template>
      <p>来源：{{ preview.source }}</p>
      <p v-if="preview.price_breakdown">折扣后单价：{{ (preview.price_breakdown as Record<string, string>).final_unit_price_after_discount }}</p>
      <p v-if="preview.quote_model?.final_quote_stage">行项目小计：{{ preview.quote_model.final_quote_stage.line_subtotal }}</p>
      <el-alert
        v-if="preview.quote_model"
        type="info"
        show-icon
        :closable="false"
        :title="preview.quote_model.customer_safe_boundary"
      />
    </el-card>
  </div>
</template>

<style scoped>
.page { padding: 16px; }
.mb { margin-bottom: 16px; }
.form { max-width: 640px; }
</style>
