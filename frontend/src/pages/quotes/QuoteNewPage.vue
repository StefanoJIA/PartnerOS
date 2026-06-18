<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  fetchCatalogProducts,
  postPricingPreview,
  type CatalogProduct,
  type IntervalQuoteRow,
  type PricingPreviewResult,
} from '@/api/quoteCatalog'
import { http } from '@/api/http'

const router = useRouter()
const products = ref<CatalogProduct[]>([])
const productId = ref('')
const quantity = ref(50)
const incoterm = ref('FOB')
const strategy = ref('volume')
const preview = ref<PricingPreviewResult | null>(null)
const loading = ref(false)
const previewLoading = ref(false)
const error = ref('')
const billToCompany = ref('')

const SAFETY =
  '创建报价只会保存内部报价记录和报价模型快照，不会自动发送邮件、不会通知客户、不会承诺库存、认证或交期。成本、利润、物流测算和区间价来源保持内部可见。'

const selectedProduct = computed(() => products.value.find((item) => item.id === productId.value) ?? null)
const intervalRows = computed<IntervalQuoteRow[]>(() => {
  const stage = preview.value?.quote_model?.final_quote_stage as { interval_quote_table?: IntervalQuoteRow[] } | undefined
  return stage?.interval_quote_table ?? []
})
const selectedInterval = computed(() => {
  return intervalRows.value.find((row) => {
    const max = row.max_qty ?? Number.POSITIVE_INFINITY
    return quantity.value >= row.min_qty && quantity.value <= max
  })
})
const canCreate = computed(() => Boolean(productId.value && selectedProduct.value && !loading.value))

function price(value: string | null | undefined, currency = 'USD') {
  return value ? `${value} ${currency}` : 'N/A'
}

async function loadProducts() {
  const data = await fetchCatalogProducts({ limit: 200 })
  products.value = data.items
  if (data.items.length && !productId.value) productId.value = data.items[0].id
}

async function runPreview() {
  if (!productId.value) {
    error.value = '请选择产品后再预览区间报价。'
    return
  }
  previewLoading.value = true
  error.value = ''
  try {
    preview.value = await postPricingPreview({
      product_id: productId.value,
      quantity: quantity.value,
      incoterm: incoterm.value,
      pricing_strategy: strategy.value,
    })
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '区间报价预览失败，请检查产品价目表、汇率和贸易条款。'
  } finally {
    previewLoading.value = false
  }
}

async function createQuote() {
  if (!productId.value) {
    error.value = '请选择产品后再创建报价。'
    return
  }
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
    } else {
      error.value = '报价已提交但没有返回报价 ID，请刷新报价列表确认。'
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '创建报价失败'
  } finally {
    loading.value = false
  }
}

watch([productId, quantity, incoterm, strategy], () => {
  preview.value = null
})

onMounted(async () => {
  try {
    await loadProducts()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '产品加载失败，请确认 backend 已启动并且产品目录可用。'
  }
})
</script>

<template>
  <div class="page">
    <el-button link @click="router.push({ name: 'quotes' })">返回报价列表</el-button>
    <h1>新建报价</h1>
    <el-alert type="warning" :closable="false" show-icon title="安全边界" :description="SAFETY" class="mb" />
    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />

    <el-form label-width="140px" class="form">
      <el-form-item label="客户公司">
        <el-input v-model="billToCompany" placeholder="客户公司名称" />
      </el-form-item>
      <el-form-item label="产品">
        <el-select v-model="productId" filterable placeholder="请选择产品" style="width: 100%">
          <el-option
            v-for="p in products"
            :key="p.id"
            :label="`${p.internal_sku} - ${p.product_name}`"
            :value="p.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="参考数量">
        <el-input-number v-model="quantity" :min="1" />
        <span class="hint">仅用于内部校验当前落在哪个价格区间；客户报价会呈现该产品完整区间价表，下单后才计算准确总价。</span>
      </el-form-item>
      <el-form-item label="贸易条款">
        <el-select v-model="incoterm">
          <el-option label="FOB" value="FOB" />
          <el-option label="DDP" value="DDP" />
        </el-select>
      </el-form-item>
      <el-form-item label="报价策略">
        <el-select v-model="strategy">
          <el-option label="销售" value="volume" />
          <el-option label="引流" value="traffic" />
          <el-option label="利润" value="profit" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button :loading="previewLoading" @click="runPreview">预览区间报价</el-button>
        <el-button type="primary" :loading="loading" :disabled="!canCreate" @click="createQuote">创建报价</el-button>
      </el-form-item>
    </el-form>

    <el-card v-if="preview" shadow="never" class="mb">
      <template #header>
        <div class="card-title">
          <span>产品区间报价表</span>
          <el-tag effect="plain">{{ preview.source }}</el-tag>
        </div>
      </template>
      <p class="summary">
        {{ selectedProduct?.product_name || preview.product_id }}：每个产品按自己的完整数量区间报价，FOB/DDP 不可用时显示 N/A；客户选择下单数量后才形成订单总价。
      </p>
      <el-table v-if="intervalRows.length" :data="intervalRows" size="small" border>
        <el-table-column prop="quantity_label" label="数量区间" width="140" />
        <el-table-column label="FOB 单价">
          <template #default="{ row }">{{ price(row.fob_unit_price, row.currency) }}</template>
        </el-table-column>
        <el-table-column label="DDP 单价">
          <template #default="{ row }">{{ price(row.ddp_unit_price, row.currency) }}</template>
        </el-table-column>
        <el-table-column label="可用条款">
          <template #default="{ row }">{{ row.incoterms_available.join(' / ') || '-' }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="该产品还没有可用的区间价目表" />
      <div v-if="selectedInterval" class="selected-range">
        当前参考数量 {{ quantity }} 落在 {{ selectedInterval.quantity_label }} 区间；
        {{ incoterm }} 参考单价：
        {{ price(incoterm === 'DDP' ? selectedInterval.ddp_unit_price : selectedInterval.fob_unit_price, selectedInterval.currency) }}
      </div>
      <p v-if="preview.quote_model?.final_quote_stage" class="summary">
        内部参考校验小计（非客户最终总价）：{{ preview.quote_model.final_quote_stage.line_subtotal }}
      </p>
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
.form { max-width: 760px; }
.hint { margin-left: 12px; color: var(--el-text-color-secondary); font-size: 12px; }
.card-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.summary { color: var(--el-text-color-secondary); margin: 0 0 12px; }
.selected-range {
  margin: 12px 0;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  background: var(--el-fill-color-light);
}
</style>
