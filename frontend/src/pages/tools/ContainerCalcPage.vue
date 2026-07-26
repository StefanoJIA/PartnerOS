<template>
  <div class="container-calc-page">
    <header class="page-header">
      <div>
        <h1>托盘与装柜计算</h1>
        <p>按 IntelliOpus 当前海运托盘规则估算包装箱摆放、堆叠层数、托盘数量和 40HQ 占用。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="calculate">计算托盘方案</el-button>
    </header>

    <el-alert
      type="info"
      show-icon
      :closable="false"
      title="规划边界"
      description="当前只做内部装柜估算，不会创建 shipment、不会通知承运商、不会自动生成订单。木托盘出口前仍需确认 ISPM 15 等合规要求。"
      class="notice"
    />

    <section class="config-grid">
      <div class="config-panel">
        <h2>标准托盘参数</h2>
        <div class="param-grid">
          <el-form-item label="托盘长 cm">
            <el-input-number v-model="standard.pallet_length_cm" :min="1" />
          </el-form-item>
          <el-form-item label="托盘宽 cm">
            <el-input-number v-model="standard.pallet_width_cm" :min="1" />
          </el-form-item>
          <el-form-item label="托盘高度 cm">
            <el-input-number v-model="standard.pallet_height_cm" :min="0" />
          </el-form-item>
          <el-form-item label="整托最高 cm">
            <el-input-number v-model="standard.max_total_height_cm" :min="1" />
          </el-form-item>
          <el-form-item label="连续堆叠层数">
            <el-input-number v-model="standard.max_continuous_layers" :min="1" />
          </el-form-item>
          <el-form-item label="40HQ 参考 CBM">
            <el-input-number v-model="standard.container_cbm" :min="1" />
          </el-form-item>
        </div>
        <p class="config-note">
          当前默认：120×100cm 标准托盘、托盘高度 20cm、整托最高 200cm、连续堆叠不超过 8 层。
        </p>
      </div>

      <div class="config-panel">
        <div class="panel-title">
          <h2>包装箱规格</h2>
          <el-button plain @click="addCarton">新增包装箱</el-button>
        </div>
        <div v-for="(carton, index) in cartons" :key="carton.local_id" class="carton-row">
          <el-input v-model="carton.label" placeholder="包装箱名称，例如主箱 / 配件箱" />
          <el-input-number v-model="carton.length_cm" :min="1" placeholder="长" />
          <el-input-number v-model="carton.width_cm" :min="1" placeholder="宽" />
          <el-input-number v-model="carton.height_cm" :min="1" placeholder="高" />
          <el-input-number v-model="carton.cartons" :min="1" placeholder="箱数" />
          <el-input-number v-model="carton.weight_kg" :min="0" placeholder="kg" />
          <el-button type="danger" plain :disabled="cartons.length === 1" @click="removeCarton(index)">删除</el-button>
        </div>
        <div class="carton-head">
          <span>名称</span>
          <span>长 cm</span>
          <span>宽 cm</span>
          <span>高 cm</span>
          <span>箱数</span>
          <span>单箱 kg</span>
          <span>操作</span>
        </div>
      </div>
    </section>

    <el-alert v-if="error" type="error" :title="error" show-icon class="notice" />

    <section v-if="result" class="result-section">
      <div class="summary-grid">
        <div class="summary-card">
          <span>总体 CBM</span>
          <strong>{{ result.summary.total_cbm }}</strong>
        </div>
        <div class="summary-card">
          <span>40HQ 占用</span>
          <strong>{{ formatPercent(result.summary.approx_container_load) }}</strong>
        </div>
        <div class="summary-card">
          <span>地面托盘位</span>
          <strong>{{ result.summary.pallet_positions }}</strong>
        </div>
        <div class="summary-card">
          <span>物理托盘数</span>
          <strong>{{ result.summary.physical_pallets }}</strong>
        </div>
      </div>

      <article v-for="plan in result.plans" :key="plan.label" class="plan-card" :class="{ blocked: plan.status !== 'ok' }">
        <div class="plan-main">
          <div>
            <h3>{{ plan.label }}</h3>
            <p v-if="plan.status === 'ok'">
              每层 {{ plan.cartons_per_layer }} 箱 · 满托 {{ plan.layers_per_full_pallet }} 层 /
              {{ plan.cartons_per_full_pallet }} 箱 · 满托高度 {{ plan.full_pallet_height_cm }}cm
            </p>
            <p v-else>{{ plan.reason }}</p>
            <div class="tags">
              <el-tag v-if="plan.status === 'ok'" type="success">可装托</el-tag>
              <el-tag v-else type="danger">需复核</el-tag>
              <el-tag effect="plain">{{ plan.total_cbm }} CBM</el-tag>
              <el-tag effect="plain">{{ plan.pallet_positions }} 个托盘位</el-tag>
              <el-tag effect="plain">{{ plan.physical_pallets }} 个物理托盘</el-tag>
            </div>
          </div>
          <div v-if="plan.status === 'ok'" class="orientation">
            <strong>最佳摆放</strong>
            <span>
              {{ plan.best_orientation.orientation === 'rotated' ? '旋转摆放' : '正常摆放' }}：
              {{ plan.best_orientation.along_length }} × {{ plan.best_orientation.along_width }}
            </span>
          </div>
        </div>

        <div v-if="plan.status === 'ok'" class="visual-row">
          <div v-for="(unit, idx) in previewUnits(plan)" :key="`${plan.label}-${idx}`" class="pallet-visual">
            <div class="height-label">{{ unit.gross_height_cm }}cm</div>
            <div class="stack">
              <template v-for="(segment, segIdx) in unit.layer_segments" :key="`${idx}-${segIdx}`">
                <div v-if="segIdx > 0" class="middle-pallet">中间托盘</div>
                <div
                  v-for="layer in segment"
                  :key="`${idx}-${segIdx}-${layer}`"
                  class="box-layer"
                  :style="{ animationDelay: `${(segIdx * 4 + layer) * 40}ms` }"
                />
              </template>
              <div class="base-pallet">底托</div>
            </div>
            <span>第 {{ idx + 1 }} 托：{{ unit.cartons }} 箱 / {{ unit.layers }} 层</span>
          </div>
        </div>

        <ul v-if="plan.warnings?.length" class="warnings">
          <li v-for="warning in plan.warnings" :key="warning">{{ warning }}</li>
        </ul>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { http } from '@/api/http'

type CartonForm = {
  local_id: string
  label: string
  length_cm: number
  width_cm: number
  height_cm: number
  cartons: number
  weight_kg: number | null
}

type PalletUnit = {
  cartons: number
  layers: number
  layer_segments: number[]
  divider_pallets: number
  gross_height_cm: number
  physical_pallets: number
}

type PalletPlan = {
  label: string
  status: string
  reason?: string
  total_cbm: number
  cartons_per_layer: number
  layers_per_full_pallet: number
  cartons_per_full_pallet: number
  full_pallet_height_cm: number
  best_orientation: {
    orientation: string
    along_length: number
    along_width: number
  }
  pallet_positions: number
  physical_pallets: number
  pallet_units: PalletUnit[]
  warnings: string[]
}

type PalletPlanResult = {
  summary: {
    total_cbm: number
    approx_container_load: number
    pallet_positions: number
    physical_pallets: number
    blocked_specs: number
  }
  plans: PalletPlan[]
}

const standard = reactive({
  pallet_length_cm: 120,
  pallet_width_cm: 100,
  pallet_height_cm: 20,
  max_total_height_cm: 200,
  max_continuous_layers: 8,
  container_cbm: 68,
})

const cartons = ref<CartonForm[]>([
  {
    local_id: crypto.randomUUID(),
    label: '主包装箱',
    length_cm: 60,
    width_cm: 50,
    height_cm: 16,
    cartons: 60,
    weight_kg: null,
  },
])
const result = ref<PalletPlanResult | null>(null)
const loading = ref(false)
const error = ref('')

function addCarton() {
  cartons.value.push({
    local_id: crypto.randomUUID(),
    label: `包装箱 ${cartons.value.length + 1}`,
    length_cm: 60,
    width_cm: 50,
    height_cm: 20,
    cartons: 20,
    weight_kg: null,
  })
}

function removeCarton(index: number) {
  cartons.value.splice(index, 1)
}

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`
}

function previewUnits(plan: PalletPlan) {
  return plan.pallet_units.slice(0, 4)
}

async function calculate() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await http.post('/container-calculator/pallet-plan', {
      ...standard,
      carton_specs: cartons.value.map(({ local_id: _localId, ...carton }) => carton),
    })
    result.value = data
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '托盘方案计算失败，请确认 backend 正常运行。'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.container-calc-page {
  padding: 24px;
  color: #0f172a;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.page-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
}

.page-header p,
.config-note {
  margin: 0;
  color: #64748b;
}

.notice {
  margin: 16px 0;
}

.config-grid {
  display: grid;
  grid-template-columns: minmax(280px, 420px) minmax(520px, 1fr);
  gap: 16px;
}

.config-panel,
.plan-card,
.summary-card {
  border: 1px solid #dbe4f0;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.config-panel h2,
.plan-card h3 {
  margin: 0 0 12px;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 12px;
}

.panel-title,
.plan-main {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.carton-head,
.carton-row {
  display: grid;
  grid-template-columns: minmax(160px, 1.5fr) repeat(5, minmax(96px, 1fr)) 80px;
  gap: 8px;
  align-items: center;
}

.carton-head {
  margin-top: 8px;
  color: #64748b;
  font-size: 12px;
}

.carton-row {
  margin: 8px 0;
}

.result-section {
  margin-top: 20px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.summary-card span {
  display: block;
  color: #64748b;
}

.summary-card strong {
  display: block;
  margin-top: 6px;
  font-size: 28px;
}

.plan-card {
  margin-bottom: 14px;
}

.plan-card.blocked {
  border-color: #fecaca;
  background: #fff7f7;
}

.plan-main p {
  margin: 0 0 10px;
  color: #64748b;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.orientation {
  min-width: 220px;
  color: #334155;
}

.orientation strong,
.orientation span {
  display: block;
}

.visual-row {
  display: flex;
  gap: 18px;
  overflow-x: auto;
  padding: 20px 0 6px;
}

.pallet-visual {
  width: 150px;
  text-align: center;
  color: #475569;
  font-size: 12px;
}

.height-label {
  margin-bottom: 4px;
  color: #1d4ed8;
  font-weight: 700;
}

.stack {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  min-height: 190px;
  padding: 8px 18px;
  border: 1px dashed #93c5fd;
  background: linear-gradient(180deg, #eff6ff 0%, #fff 100%);
  border-radius: 8px;
}

.box-layer {
  height: 12px;
  margin-top: 2px;
  border: 1px solid #bfdbfe;
  background: #60a5fa;
  animation: layer-rise 420ms ease both;
}

.middle-pallet,
.base-pallet {
  height: 12px;
  margin-top: 3px;
  border-radius: 2px;
  background: #1e3a8a;
  color: #fff;
  font-size: 10px;
  line-height: 12px;
}

.base-pallet {
  height: 16px;
  line-height: 16px;
}

.warnings {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #92400e;
}

@keyframes layer-rise {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1100px) {
  .config-grid,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .carton-head {
    display: none;
  }

  .carton-row {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
