<template>
  <div v-loading="loading" class="space-y-4">
    <el-button link type="primary" @click="$router.push({ name: 'partners' })">← 制造伙伴列表</el-button>

    <template v-if="ws && partner">
      <el-card shadow="never">
        <h2 class="text-xl font-semibold">{{ partner.partner_name }}</h2>
        <p class="text-sm text-slate-600">
          {{ partner.partner_type }} · {{ partner.country || '—' }} / {{ partner.province || '' }} {{ partner.city || '' }}
        </p>
        <p class="mt-2 text-sm">法人 {{ partner.legal_name || '—' }} · 品牌 {{ partner.brand_name || '—' }}</p>
        <p class="text-sm">网站 {{ partner.website || '—' }}</p>
        <p class="text-sm">联系人 {{ partner.contact_person || '—' }} · {{ partner.contact_email || '—' }} · {{ partner.phone || '—' }}</p>
        <p class="mt-2 whitespace-pre-wrap text-sm">{{ partner.address || '' }}</p>
        <p class="mt-2 text-sm font-medium text-slate-700">能力与政策</p>
        <p class="whitespace-pre-wrap text-sm">{{ partner.factory_locations || '—' }}</p>
        <p class="whitespace-pre-wrap text-sm">{{ partner.main_product_categories || '—' }}</p>
        <p class="whitespace-pre-wrap text-sm">{{ partner.manufacturing_capabilities || '—' }}</p>
        <p class="whitespace-pre-wrap text-sm">OEM/ODM {{ partner.oem_odm_capability || '—' }}</p>
        <p class="whitespace-pre-wrap text-sm">定制 {{ partner.customization_capability || '—' }}</p>
        <p class="whitespace-pre-wrap text-sm">MOQ {{ partner.moq_policy || '—' }} · 样品 {{ partner.sample_policy || '—' }} · 交期 {{ partner.lead_time || '—' }}</p>
        <p class="whitespace-pre-wrap text-sm">{{ partner.export_experience || '—' }}</p>
        <p class="whitespace-pre-wrap text-sm">美国市场 {{ partner.us_market_experience || '—' }}</p>
        <p class="text-sm">英文资料 {{ partner.english_materials_available === null ? '—' : partner.english_materials_available ? '是' : '否' }}</p>
        <p class="text-sm">价格带 {{ partner.price_level || '—' }} · 风险 {{ partner.risk_level || '—' }}</p>
      </el-card>

      <el-card shadow="never">
        <template #header>RFQ / 报价</template>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <div class="mb-1 text-sm font-medium text-slate-700">关联 RFQ</div>
            <el-table v-if="relatedRfqs.length" :data="relatedRfqs" size="small">
              <el-table-column label="#">
                <template #default="{ row }">
                  <router-link class="text-blue-600" :to="{ name: 'rfq-detail', params: { rfqId: row.id } }">{{
                    row.rfq_number
                  }}</router-link>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" />
            </el-table>
            <p v-else class="text-xs text-slate-500">暂无</p>
          </div>
          <div>
            <div class="mb-1 text-sm font-medium text-slate-700">报价记录</div>
            <el-table v-if="relatedQuotes.length" :data="relatedQuotes" size="small">
              <el-table-column prop="rfq_id" label="RFQ" />
              <el-table-column prop="unit_price" label="单价" />
              <el-table-column prop="lead_time" label="交期" />
            </el-table>
            <p v-else class="text-xs text-slate-500">暂无</p>
          </div>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>评分（1–5 整数，可空）</template>
        <el-form :inline="true" class="flex flex-wrap gap-2" @submit.prevent="saveScores">
          <el-form-item label="质量"><el-input-number v-model="scores.quality_rating" :min="1" :max="5" /></el-form-item>
          <el-form-item label="沟通"><el-input-number v-model="scores.communication_rating" :min="1" :max="5" /></el-form-item>
          <el-form-item label="交付"><el-input-number v-model="scores.delivery_rating" :min="1" :max="5" /></el-form-item>
          <el-form-item label="项目匹配"><el-input-number v-model="scores.project_fit_rating" :min="1" :max="5" /></el-form-item>
          <el-form-item label="产品匹配"><el-input-number v-model="scores.product_fit_rating" :min="1" :max="5" /></el-form-item>
          <el-form-item label="认证准备度"><el-input-number v-model="scores.certification_readiness" :min="1" :max="5" /></el-form-item>
          <el-form-item label="风险等级"><el-input v-model="scores.risk_level" class="w-28" /></el-form-item>
          <el-form-item><el-button type="primary" native-type="submit">保存评分</el-button></el-form-item>
        </el-form>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <span>关联产品</span>
            <el-button size="small" type="primary" @click="linkDialog = true">添加产品</el-button>
          </div>
        </template>
        <el-table :data="linkRows" size="small" stripe>
          <el-table-column label="产品">
            <template #default="{ row }">
              <router-link class="text-blue-600" :to="{ name: 'product-detail', params: { productId: row.link.product_id } }">{{
                row.product?.product_name
              }}</router-link>
            </template>
          </el-table-column>
          <el-table-column prop="link.capability_level" label="能力" width="90" />
          <el-table-column prop="link.partner_moq" label="MOQ" width="70" />
          <el-table-column prop="link.lead_time_days" label="交期天" width="80" />
          <el-table-column prop="link.partner_price_range" label="价格带" />
          <el-table-column label="样品" width="70">
            <template #default="{ row }">{{ row.link.sample_available === true ? '是' : row.link.sample_available === false ? '否' : '—' }}</template>
          </el-table-column>
          <el-table-column prop="link.certification_status" label="认证" />
          <el-table-column label="优选" width="60">
            <template #default="{ row }">{{ row.link.is_preferred ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="removeLink(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never">
        <template #header>质量文件</template>
        <el-table v-if="qualityDocs.length" :data="qualityDocs" size="small">
          <el-table-column prop="document_type" label="类型" />
          <el-table-column prop="expiry_date" label="到期" />
          <el-table-column prop="notes" label="备注" />
        </el-table>
        <p v-else class="text-sm text-slate-500">暂无（可用伙伴文件挂载补充）</p>
      </el-card>

      <div id="ai-panel">
        <ObjectAiActionsPanel
          object-type="manufacturing_partner"
          :object-id="partnerId"
          variant="manufacturing_partner"
          :ai-context="aiContext"
        />
      </div>
      <div class="mt-4">
        <ObjectInteractionsPanel object-type="manufacturing_partner" :object-id="partnerId" @task-spawned="reload" />
      </div>
      <div class="mt-4">
        <ObjectTasksPanel ref="tasksRef" object-type="manufacturing_partner" :object-id="partnerId" />
      </div>
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <ObjectNotesPanel object-type="manufacturing_partner" :object-id="partnerId" />
        <ObjectTagsPanel object-type="manufacturing_partner" :object-id="partnerId" />
        <ObjectFilesPanel object-type="manufacturing_partner" :object-id="partnerId" />
        <div class="lg:col-span-2">
          <ObjectActivityLogPanel ref="activityRef" object-type="manufacturing_partner" :object-id="partnerId" />
        </div>
      </div>
    </template>

    <el-dialog v-model="linkDialog" title="关联产品" width="520px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="产品 ID"><el-input v-model="linkForm.product_id" /></el-form-item>
        <el-form-item label="能力等级"><el-input v-model="linkForm.capability_level" /></el-form-item>
        <el-form-item label="MOQ"><el-input-number v-model="linkForm.partner_moq" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="交期(天)"><el-input-number v-model="linkForm.lead_time_days" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="价格带"><el-input v-model="linkForm.partner_price_range" /></el-form-item>
        <el-form-item label="样品可用">
          <el-select v-model="linkForm.sample_available" clearable placeholder="未填" class="w-full">
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="认证状态"><el-input v-model="linkForm.certification_status" /></el-form-item>
        <el-form-item label="优选"><el-switch v-model="linkForm.is_preferred" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="linkForm.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="linkDialog = false">取消</el-button>
        <el-button type="primary" @click="saveLink">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialog" title="编辑关联" width="520px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="能力等级"><el-input v-model="editForm.capability_level" /></el-form-item>
        <el-form-item label="MOQ"><el-input-number v-model="editForm.partner_moq" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="交期(天)"><el-input-number v-model="editForm.lead_time_days" :min="0" class="w-full" /></el-form-item>
        <el-form-item label="价格带"><el-input v-model="editForm.partner_price_range" /></el-form-item>
        <el-form-item label="样品可用">
          <el-select v-model="editForm.sample_available" clearable class="w-full">
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="认证状态"><el-input v-model="editForm.certification_status" /></el-form-item>
        <el-form-item label="优选"><el-switch v-model="editForm.is_preferred" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="editForm.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { http } from '@/api/http'
import { fetchPartnerWorkspace } from '@/api/objectWorkspaces'
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
const partnerId = computed(() => route.params.partnerId as string)

const loading = ref(false)
const ws = ref<Record<string, unknown> | null>(null)
const tasksRef = ref<{ reload?: () => Promise<void> } | null>(null)
const activityRef = ref<{ reload?: () => void } | null>(null)

const partner = computed(() => (ws.value?.partner as Record<string, unknown> | undefined) ?? null)
const linkRows = computed(() => (ws.value?.partner_rows as { link: Record<string, unknown>; product: Record<string, unknown> }[]) ?? [])
const qualityDocs = computed(() => (ws.value?.quality_documents as Record<string, unknown>[]) ?? [])
const relatedRfqs = computed(() => (ws.value?.related_rfqs as Record<string, unknown>[]) ?? [])
const relatedQuotes = computed(() => (ws.value?.related_quotations as Record<string, unknown>[]) ?? [])

const aiContext = computed(() => ({ ...(partner.value ?? {}) }))

const scores = reactive({
  quality_rating: undefined as number | undefined,
  communication_rating: undefined as number | undefined,
  delivery_rating: undefined as number | undefined,
  project_fit_rating: undefined as number | undefined,
  product_fit_rating: undefined as number | undefined,
  certification_readiness: undefined as number | undefined,
  risk_level: '' as string | undefined,
})

const linkDialog = ref(false)
const linkForm = reactive({
  product_id: '',
  is_preferred: false,
  capability_level: '',
  partner_moq: undefined as number | undefined,
  lead_time_days: undefined as number | undefined,
  partner_price_range: '',
  sample_available: undefined as boolean | undefined,
  certification_status: '',
  notes: '',
})

const editDialog = ref(false)
const editingProductId = ref('')
const editForm = reactive({
  is_preferred: false,
  capability_level: '',
  partner_moq: undefined as number | undefined,
  lead_time_days: undefined as number | undefined,
  partner_price_range: '',
  sample_available: undefined as boolean | undefined,
  certification_status: '',
  notes: '',
})

function syncScoresFromPartner() {
  const p = partner.value
  if (!p) return
  scores.quality_rating = (p.quality_rating as number | undefined) ?? undefined
  scores.communication_rating = (p.communication_rating as number | undefined) ?? undefined
  scores.delivery_rating = (p.delivery_rating as number | undefined) ?? undefined
  scores.project_fit_rating = (p.project_fit_rating as number | undefined) ?? undefined
  scores.risk_level = (p.risk_level as string | undefined) || ''
  const ex = (p.extra_scores as Record<string, number> | null) || {}
  scores.product_fit_rating = ex.product_fit_rating
  scores.certification_readiness = ex.certification_readiness
}

async function reload() {
  ws.value = await fetchPartnerWorkspace(partnerId.value)
  syncScoresFromPartner()
  tasksRef.value?.reload?.()
  activityRef.value?.reload?.()
}

async function load() {
  loading.value = true
  try {
    ws.value = await fetchPartnerWorkspace(partnerId.value)
    syncScoresFromPartner()
  } finally {
    loading.value = false
  }
}

async function saveScores() {
  await http.post(`/manufacturing-partners/${partnerId.value}/score`, { ...scores })
  ElMessage.success('评分已保存')
  await reload()
}

async function saveLink() {
  await http.post(`/manufacturing-partners/${partnerId.value}/products`, { ...linkForm })
  ElMessage.success('已关联')
  linkDialog.value = false
  await reload()
}

function openEdit(row: { link: Record<string, unknown> }) {
  editingProductId.value = String(row.link.product_id)
  editForm.is_preferred = !!row.link.is_preferred
  editForm.capability_level = (row.link.capability_level as string) || ''
  editForm.partner_moq = row.link.partner_moq as number | undefined
  editForm.lead_time_days = row.link.lead_time_days as number | undefined
  editForm.partner_price_range = (row.link.partner_price_range as string) || ''
  editForm.sample_available = row.link.sample_available as boolean | undefined
  editForm.certification_status = (row.link.certification_status as string) || ''
  editForm.notes = (row.link.notes as string) || ''
  editDialog.value = true
}

async function saveEdit() {
  await http.put(`/manufacturing-partners/${partnerId.value}/products/${editingProductId.value}`, { ...editForm })
  ElMessage.success('已更新')
  editDialog.value = false
  await reload()
}

async function removeLink(row: { link: Record<string, unknown> }) {
  await ElMessageBox.confirm('移除此产品关联？', '确认')
  await http.delete(`/manufacturing-partners/${partnerId.value}/products/${row.link.product_id}`)
  ElMessage.success('已移除')
  await reload()
}

watch(partnerId, () => load())
onMounted(load)
</script>
