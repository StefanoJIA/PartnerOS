<template>
  <div v-loading="loading" class="space-y-4">
    <el-button link type="primary" @click="$router.push({ name: 'products' })">← 产品列表</el-button>

    <template v-if="ws && product">
      <el-card shadow="never">
        <h2 class="text-xl font-semibold">{{ product.product_name }}</h2>
        <p class="text-sm text-slate-600">{{ product.product_category || '—' }} · {{ product.product_subcategory || '—' }}</p>
        <p class="mt-2 whitespace-pre-wrap text-sm">{{ product.description || '—' }}</p>
        <p class="mt-2 whitespace-pre-wrap text-sm font-medium text-slate-700">要点 / 场景 / 客群</p>
        <p class="whitespace-pre-wrap text-sm">{{ product.key_features || '—' }}</p>
        <p class="whitespace-pre-wrap text-sm">{{ product.application_scenarios || '—' }}</p>
        <p class="whitespace-pre-wrap text-sm">{{ product.target_customer_types || '—' }}</p>
        <p class="mt-2 text-sm">规格：尺寸 {{ product.dimensions || '—' }} · 重量 {{ product.weight || '—' }} · 载重 {{ product.load_capacity || '—' }}</p>
        <p class="text-sm">物料/表面 {{ product.material || '—' }} / {{ product.finish || '—' }} · 颜色 {{ product.color_options || '—' }}</p>
        <p class="text-sm">MOQ {{ product.moq ?? '—' }} · 样品 {{ product.sample_available }} · 样品费 {{ product.sample_cost ?? '—' }}</p>
        <p class="text-sm">FOB {{ product.fob_price_range || '—' }} · 目标美国价 {{ product.target_us_price_range || '—' }}</p>
        <p class="text-sm">包装 {{ product.packaging_dimensions || '—' }} · 箱重 {{ product.carton_weight || '—' }}</p>
        <p class="whitespace-pre-wrap text-sm">{{ product.pallet_info || '' }}</p>
        <p class="text-sm">
          柜量 20GP {{ product.container_loading_20gp || '—' }} · 40GP {{ product.container_loading_40gp || '—' }} · 40HQ
          {{ product.container_loading_40hq || '—' }}
        </p>
      </el-card>

      <el-card shadow="never">
        <template #header>应用 / 市场 fit（文本字段）</template>
        <p class="text-sm">{{ product.application_scenarios || '—' }}</p>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <span>关联制造伙伴</span>
            <el-button size="small" type="primary" @click="partnerDialog = true">添加伙伴</el-button>
          </div>
        </template>
        <el-table :data="partnerRows" size="small" stripe>
          <el-table-column label="伙伴">
            <template #default="{ row }">
              <router-link class="text-blue-600" :to="{ name: 'partner-detail', params: { partnerId: row.partner.id } }">{{
                row.partner.partner_name
              }}</router-link>
            </template>
          </el-table-column>
          <el-table-column prop="partner.partner_type" label="类型" width="100" />
          <el-table-column prop="link.capability_level" label="能力" width="90" />
          <el-table-column prop="link.partner_moq" label="MOQ" width="70" />
          <el-table-column prop="link.lead_time_days" label="交期" width="70" />
          <el-table-column prop="link.partner_price_range" label="价格带" />
          <el-table-column label="样品" width="60">
            <template #default="{ row }">{{ row.link.sample_available === true ? '是' : '—' }}</template>
          </el-table-column>
          <el-table-column prop="link.certification_status" label="认证" />
          <el-table-column label="优选" width="60">
            <template #default="{ row }">{{ row.link.is_preferred ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openPartnerEdit(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="removePartner(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="comparison" shadow="never">
        <template #header>伙伴对比（规则）</template>
        <ul class="list-inside list-disc text-sm text-slate-700">
          <li>最佳样品支持：{{ nameFor(comparison.best_for_sample_partner_id) }}</li>
          <li>较低 MOQ：{{ nameFor(comparison.best_for_low_moq_partner_id) }}</li>
          <li>定制能力：{{ nameFor(comparison.best_for_customization_partner_id) }}</li>
          <li>认证准备：{{ nameFor(comparison.best_for_certification_partner_id) }}</li>
        </ul>
      </el-card>

      <div id="ai-panel">
        <ObjectAiActionsPanel object-type="product" :object-id="productId" variant="product" :ai-context="aiContext" />
      </div>
      <div class="mt-4">
        <ObjectInteractionsPanel object-type="product" :object-id="productId" @task-spawned="reload" />
      </div>
      <div class="mt-4">
        <ObjectTasksPanel ref="tasksRef" object-type="product" :object-id="productId" />
      </div>
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <ObjectNotesPanel object-type="product" :object-id="productId" />
        <ObjectTagsPanel object-type="product" :object-id="productId" />
        <ObjectFilesPanel object-type="product" :object-id="productId" />
        <div class="lg:col-span-2">
          <ObjectActivityLogPanel ref="activityRef" object-type="product" :object-id="productId" />
        </div>
      </div>
    </template>

    <el-dialog v-model="partnerDialog" title="添加制造伙伴" width="520px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="伙伴 ID"><el-input v-model="pForm.manufacturing_partner_id" /></el-form-item>
        <el-form-item label="能力等级"><el-input v-model="pForm.capability_level" /></el-form-item>
        <el-form-item label="MOQ"><el-input-number v-model="pForm.partner_moq" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="交期(天)"><el-input-number v-model="pForm.lead_time_days" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="价格带"><el-input v-model="pForm.partner_price_range" /></el-form-item>
        <el-form-item label="样品可用">
          <el-select v-model="pForm.sample_available" clearable class="w-full">
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="认证状态"><el-input v-model="pForm.certification_status" /></el-form-item>
        <el-form-item label="优选"><el-switch v-model="pForm.is_preferred" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="pForm.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="partnerDialog = false">取消</el-button>
        <el-button type="primary" @click="savePartnerLink">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editPDialog" title="编辑关联" width="520px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="能力等级"><el-input v-model="editP.capability_level" /></el-form-item>
        <el-form-item label="MOQ"><el-input-number v-model="editP.partner_moq" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="交期(天)"><el-input-number v-model="editP.lead_time_days" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="价格带"><el-input v-model="editP.partner_price_range" /></el-form-item>
        <el-form-item label="样品可用">
          <el-select v-model="editP.sample_available" clearable class="w-full">
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="认证状态"><el-input v-model="editP.certification_status" /></el-form-item>
        <el-form-item label="优选"><el-switch v-model="editP.is_preferred" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="editP.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editPDialog = false">取消</el-button>
        <el-button type="primary" @click="savePartnerEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { http } from '@/api/http'
import { fetchProductWorkspace } from '@/api/objectWorkspaces'
import {
  ObjectActivityLogPanel,
  ObjectAiActionsPanel,
  ObjectFilesPanel,
  ObjectInteractionsPanel,
  ObjectNotesPanel,
  ObjectTagsPanel,
  ObjectTasksPanel,
} from '@/components/object-panels'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const productId = computed(() => route.params.productId as string)

const loading = ref(false)
const ws = ref<Record<string, unknown> | null>(null)
const tasksRef = ref<{ reload?: () => Promise<void> } | null>(null)
const activityRef = ref<{ reload?: () => void } | null>(null)

const product = computed(() => (ws.value?.product as Record<string, unknown> | undefined) ?? null)
const partnerRows = computed(
  () => (ws.value?.partner_rows as { link: Record<string, unknown>; partner: Record<string, unknown> }[]) ?? []
)
const comparison = computed(() => (ws.value?.partner_comparison as Record<string, string | null> | undefined) ?? null)

const nameByPartnerId = computed(() => {
  const m: Record<string, string> = {}
  for (const r of partnerRows.value) {
    m[String(r.partner.id)] = String(r.partner.partner_name)
  }
  return m
})

function nameFor(id: string | null | undefined) {
  if (!id) return '—'
  return nameByPartnerId.value[id] || id.slice(0, 8)
}

const aiContext = computed(() => ({ ...(product.value ?? {}) }))

const partnerDialog = ref(false)
const pForm = reactive({
  manufacturing_partner_id: '',
  is_preferred: false,
  capability_level: '',
  partner_moq: undefined as number | undefined,
  lead_time_days: undefined as number | undefined,
  partner_price_range: '',
  sample_available: undefined as boolean | undefined,
  certification_status: '',
  notes: '',
})

const editPDialog = ref(false)
const editingPartnerId = ref('')
const editP = reactive({
  is_preferred: false,
  capability_level: '',
  partner_moq: undefined as number | undefined,
  lead_time_days: undefined as number | undefined,
  partner_price_range: '',
  sample_available: undefined as boolean | undefined,
  certification_status: '',
  notes: '',
})

async function reload() {
  ws.value = await fetchProductWorkspace(productId.value)
  tasksRef.value?.reload?.()
  activityRef.value?.reload?.()
}

async function load() {
  loading.value = true
  try {
    ws.value = await fetchProductWorkspace(productId.value)
  } finally {
    loading.value = false
  }
}

async function savePartnerLink() {
  await http.post(`/products/${productId.value}/partners`, { ...pForm })
  ElMessage.success('已关联')
  partnerDialog.value = false
  await reload()
}

function openPartnerEdit(row: { link: Record<string, unknown> }) {
  editingPartnerId.value = String(row.link.manufacturing_partner_id)
  editP.is_preferred = !!row.link.is_preferred
  editP.capability_level = (row.link.capability_level as string) || ''
  editP.partner_moq = row.link.partner_moq as number | undefined
  editP.lead_time_days = row.link.lead_time_days as number | undefined
  editP.partner_price_range = (row.link.partner_price_range as string) || ''
  editP.sample_available = row.link.sample_available as boolean | undefined
  editP.certification_status = (row.link.certification_status as string) || ''
  editP.notes = (row.link.notes as string) || ''
  editPDialog.value = true
}

async function savePartnerEdit() {
  await http.put(`/products/${productId.value}/partners/${editingPartnerId.value}`, { ...editP })
  ElMessage.success('已更新')
  editPDialog.value = false
  await reload()
}

async function removePartner(row: { link: Record<string, unknown> }) {
  await ElMessageBox.confirm('移除此制造伙伴关联？', '确认')
  await http.delete(`/products/${productId.value}/partners/${row.link.manufacturing_partner_id}`)
  ElMessage.success('已移除')
  await reload()
}

watch(productId, () => load())
onMounted(load)
</script>
