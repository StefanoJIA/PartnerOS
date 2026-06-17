<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchCatalogProducts, postPricingPreview, type CatalogProduct, type PricingPreviewResult } from '@/api/quoteCatalog'

const SAFETY =
  '价格预览只做内部测算：不会创建报价、不会自动发送消息、不会承诺库存、认证或交期。成本、利润、物流测算只供内部使用。'

const loading = ref(false)
const products = ref<CatalogProduct[]>([])
const productId = ref('')
const quantity = ref(100)
const incoterm = ref('FOB')
const strategy = ref('volume')
const discountPct = ref<number | null>(null)
const result = ref<PricingPreviewResult | null>(null)
const error = ref<string | null>(null)

const flowLabels: Record<string, string> = {
  cost: '成本测算',
  logistics: '物流运输',
  fx: '汇率换算',
  price_tier: '价目表/策略',
  profit_check: '利润校验',
  customer_quote: '客户报价',
}

const sheetLabels: Record<string, string> = {
  cost: '成本',
  price_list: '价目表',
  profit_calculator: '利润计算器',
  Quote: 'Quote',
}

const strategyLabels: Record<string, string> = {
  traffic: '引流',
  volume: '销量',
  profit: '利润',
}

const selectedProduct = computed(() => products.value.find((item) => item.id === productId.value) ?? null)
const model = computed(() => result.value?.quote_model ?? null)

onMounted(async () => {
  try {
    const data = await fetchCatalogProducts({ limit: 200 })
    products.value = data.items
    if (data.items.length) productId.value = data.items[0].id
  } catch {
    error.value = '产品加载失败，请确认 backend 已启动并且产品目录可用。'
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
    error.value = '价格预览失败，请检查产品成本、价目表、汇率和数量档。'
  } finally {
    loading.value = false
  }
}

function valueOf(stage: Record<string, unknown> | undefined, key: string, fallback = '-') {
  const value = stage?.[key]
  if (value === null || value === undefined || value === '') return fallback
  return String(value)
}
</script>

<template>
  <div class="pricing-page">
    <div class="page-head">
      <div>
        <h1>报价流程预览</h1>
        <p>按 Excel 报价模型形成固定流程：成本 → 物流 → 汇率 → 价目/利润 → 最终报价 → PDF 安全输出。</p>
      </div>
      <el-tag type="warning" effect="plain">内部测算</el-tag>
    </div>

    <el-alert type="info" :closable="false" show-icon class="mb" :title="SAFETY" />

    <el-form label-width="120px" class="quote-form">
      <el-form-item label="产品">
        <el-select v-model="productId" filterable style="width: 100%">
          <el-option
            v-for="p in products"
            :key="p.id"
            :label="`${p.internal_sku} - ${p.product_name}`"
            :value="p.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="数量">
        <el-input-number v-model="quantity" :min="1" />
      </el-form-item>
      <el-form-item label="贸易条款">
        <el-select v-model="incoterm">
          <el-option label="FOB" value="FOB" />
          <el-option label="DDP" value="DDP" />
          <el-option label="EXW" value="EXW" />
          <el-option label="CIF" value="CIF" />
        </el-select>
      </el-form-item>
      <el-form-item label="报价策略">
        <el-select v-model="strategy">
          <el-option label="引流" value="traffic" />
          <el-option label="销量" value="volume" />
          <el-option label="利润" value="profit" />
        </el-select>
      </el-form-item>
      <el-form-item label="折扣 %">
        <el-input-number v-model="discountPct" :min="0" :max="100" :precision="1" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="preview">生成报价预览</el-button>
      </el-form-item>
    </el-form>

    <el-alert v-if="error" type="error" :closable="false" show-icon class="mb" :title="error" />

    <section v-if="result" class="result-layout">
      <el-card shadow="never" class="summary-card">
        <template #header>
          <div class="card-title">
            <span>最终报价</span>
            <el-tag effect="plain">{{ result.source }}</el-tag>
          </div>
        </template>
        <div class="metric-grid">
          <div>
            <span>产品</span>
            <strong>{{ selectedProduct?.product_name || result.product_id }}</strong>
          </div>
          <div>
            <span>单价</span>
            <strong>{{ result.price_breakdown?.final_unit_price_after_discount }} {{ result.currency }}</strong>
          </div>
          <div>
            <span>行项目小计</span>
            <strong>{{ result.price_breakdown?.line_subtotal }} {{ result.currency }}</strong>
          </div>
          <div>
            <span>预估毛利</span>
            <strong>{{ result.profit_breakdown?.estimated_margin }}%</strong>
          </div>
        </div>
        <el-alert
          v-if="model"
          class="mt"
          type="warning"
          :closable="false"
          show-icon
          :title="model.customer_safe_boundary"
        />
      </el-card>

      <el-card v-if="model" shadow="never" class="flow-card">
        <template #header>固定报价流程</template>
        <el-steps direction="vertical" :active="model.workflow.length" finish-status="success">
          <el-step
            v-for="step in model.workflow"
            :key="step.step"
            :title="flowLabels[step.step] || step.step"
            :description="`${sheetLabels[step.workbook_sheet] || step.workbook_sheet} / ${step.status}`"
          />
        </el-steps>
      </el-card>

      <el-card v-if="model" shadow="never">
        <template #header>成本与物流测算</template>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="物料成本 RMB">
            {{ valueOf(model.cost_stage, 'material_cost_rmb') }}
          </el-descriptions-item>
          <el-descriptions-item label="国内利润后成本 RMB">
            {{ valueOf(model.cost_stage, 'material_cost_after_domestic_profit_rmb') }}
          </el-descriptions-item>
          <el-descriptions-item label="FOB 成本 USD">
            {{ valueOf(model.cost_stage, 'fob_cost_usd') }}
          </el-descriptions-item>
          <el-descriptions-item label="DDP 成本 USD">
            {{ valueOf(model.cost_stage, 'ddp_cost_usd') }}
          </el-descriptions-item>
          <el-descriptions-item label="重量">
            {{ valueOf(model.logistics_stage, 'unit_weight') }}
          </el-descriptions-item>
          <el-descriptions-item label="运输成本">
            {{ valueOf(model.logistics_stage, 'domestic_transport_cost') }}
          </el-descriptions-item>
          <el-descriptions-item label="运费 USD">
            {{ valueOf(model.logistics_stage, 'freight_cost_usd') }}
          </el-descriptions-item>
          <el-descriptions-item label="汇率">
            {{ valueOf(model.fx_stage, 'rate') }} {{ valueOf(model.fx_stage, 'source', '') }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card v-if="model" shadow="never">
        <template #header>价目与利润校验</template>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="报价策略">
            {{ strategyLabels[result.pricing_strategy] || result.pricing_strategy }}
          </el-descriptions-item>
          <el-descriptions-item label="成本来源">
            {{ result.source }}
          </el-descriptions-item>
          <el-descriptions-item label="折扣金额">
            {{ valueOf(model.discount_stage, 'discount_amount') }}
          </el-descriptions-item>
          <el-descriptions-item label="折扣后单价">
            {{ valueOf(model.discount_stage, 'final_unit_price_after_discount') }}
          </el-descriptions-item>
          <el-descriptions-item label="预估单位利润">
            {{ valueOf(model.profit_stage, 'estimated_unit_profit') }}
          </el-descriptions-item>
          <el-descriptions-item label="预估总利润">
            {{ valueOf(model.profit_stage, 'estimated_total_profit') }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-alert
        v-for="(w, i) in result.warnings"
        :key="i"
        type="warning"
        :closable="false"
        show-icon
        :title="w"
      />
      <p class="safety-line">quote_created={{ result.safety.quote_created }} / automatic_sending_enabled={{ result.safety.automatic_sending_enabled }}</p>
    </section>
  </div>
</template>

<style scoped>
.pricing-page { padding: 16px; }
.page-head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 16px; }
.page-head h1 { margin: 0 0 6px; font-size: 22px; }
.page-head p { margin: 0; color: var(--el-text-color-secondary); }
.quote-form { max-width: 680px; }
.mb { margin-bottom: 16px; }
.mt { margin-top: 12px; }
.result-layout { display: grid; gap: 14px; margin-top: 16px; }
.card-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.metric-grid div { border: 1px solid var(--el-border-color); border-radius: 6px; padding: 10px; }
.metric-grid span { display: block; color: var(--el-text-color-secondary); font-size: 12px; margin-bottom: 4px; }
.metric-grid strong { color: var(--el-text-color-primary); }
.flow-card :deep(.el-step__description) { font-size: 12px; }
.safety-line { margin: 0; color: var(--el-text-color-secondary); font-size: 12px; }
@media (max-width: 860px) {
  .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .page-head { flex-direction: column; }
  .metric-grid { grid-template-columns: 1fr; }
}
</style>
