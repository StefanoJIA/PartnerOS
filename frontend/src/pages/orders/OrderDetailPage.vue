<template>
  <div v-loading="loading" class="space-y-4">
    <el-button link type="primary" @click="$router.push({ name: 'orders' })">← 订单列表</el-button>

    <template v-if="ws">
      <el-card shadow="never">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-slate-800">{{ ws.order.order_number }}</h2>
            <p class="mt-1 text-sm text-slate-600">
              生产：{{ ws.order.production_status || '—' }} · 海运：{{ ws.order.shipping_status || '—' }} · 风险：{{ ws.order.risk_level || '—' }}
            </p>
            <div class="mt-2 grid gap-1 text-sm text-slate-700 sm:grid-cols-2">
              <div>下单日：{{ ws.order.order_date || '—' }} · 目标交期：{{ ws.order.target_delivery_date || '—' }}</div>
              <div>金额：{{ ws.order.total_amount ?? '—' }} {{ ws.order.currency || '' }} · 条款：{{ ws.order.incoterm || '—' }}</div>
            </div>
            <p class="mt-1 text-xs text-slate-500">创建于 {{ ws.order.created_at }} · 更新 {{ ws.order.updated_at }}</p>
          </div>
          <div class="text-right text-sm text-slate-600 space-y-1">
            <div v-if="ws.company">公司：{{ ws.company.company_name }}</div>
            <div v-if="ws.contact">{{ ws.contact.first_name }} {{ ws.contact.last_name }}</div>
            <div v-if="ws.lead">线索：{{ ws.lead.lead_name }}</div>
            <div v-if="ws.rfq">RFQ：{{ ws.rfq.rfq_number }}</div>
            <div v-if="ws.quotation">报价：{{ ws.quotation.id }} @ {{ ws.quotation.unit_price ?? '—' }}</div>
            <div v-if="ws.sample">来源样品：{{ ws.sample.sample_request_number }}</div>
            <div v-if="ws.manufacturing_partner">制造伙伴：{{ ws.manufacturing_partner.partner_name }}</div>
          </div>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <el-button v-if="ws.company" size="small" @click="$router.push({ name: 'company-detail', params: { companyId: ws.company.id } })">打开公司</el-button>
          <el-button v-if="ws.contact" size="small" @click="$router.push({ name: 'contact-detail', params: { contactId: ws.contact.id } })">打开联系人</el-button>
          <el-button v-if="ws.lead" size="small" @click="$router.push({ name: 'lead-detail', params: { leadId: ws.lead.id } })">打开线索</el-button>
          <el-button v-if="ws.rfq" size="small" @click="$router.push({ name: 'rfq-detail', params: { rfqId: ws.rfq.id } })">打开 RFQ</el-button>
          <el-button v-if="ws.sample" size="small" @click="$router.push({ name: 'sample-detail', params: { sampleId: ws.sample.id } })">打开样品</el-button>
          <el-button
            v-if="ws.manufacturing_partner"
            size="small"
            @click="$router.push({ name: 'partner-detail', params: { partnerId: ws.manufacturing_partner.id } })"
          >
            打开制造伙伴
          </el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>生产状态</template>
        <div class="flex flex-wrap gap-2">
          <el-button
            v-for="st in PRODUCTION_PIPELINE"
            :key="st"
            size="small"
            :type="ws.order.production_status === st ? 'primary' : 'default'"
            @click="setProductionStatus(st)"
          >
            {{ st }}
          </el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>海运状态</template>
        <div class="flex flex-wrap gap-2">
          <el-button
            v-for="st in SHIPPING_PIPELINE"
            :key="st"
            size="small"
            :type="ws.order.shipping_status === st ? 'primary' : 'default'"
            @click="setShippingStatus(st)"
          >
            {{ st }}
          </el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>订单风险（规则）</template>
        <p class="mb-2 text-sm text-amber-800">整体：{{ ws.risk_panel?.overall_severity || '—' }}</p>
        <ul class="space-y-2 text-sm">
          <li v-for="(it, i) in ws.risk_panel?.items || []" :key="i" class="rounded border border-slate-100 p-2">
            <div class="font-medium text-slate-800">[{{ it.risk_level }}] {{ it.risk_reason }}</div>
            <div class="text-slate-600">{{ it.recommended_action }}</div>
          </li>
        </ul>
        <el-button class="mt-3" size="small" type="primary" @click="genCustomerUpdateEmail">生成客户更新邮件</el-button>
        <p v-if="customerEmailPreview" class="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded bg-slate-50 p-2 text-sm">{{ customerEmailPreview }}</p>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span>生产里程碑</span>
            <div class="flex gap-2">
              <el-button size="small" @click="generateMilestones(false)">生成里程碑</el-button>
              <el-button size="small" @click="generateMilestones(true)">强制重建里程碑</el-button>
            </div>
          </div>
        </template>
        <el-table :data="ws.production_milestones" size="small" stripe>
          <el-table-column prop="milestone_name" label="节点" min-width="140" />
          <el-table-column prop="planned_date" label="计划" width="110" />
          <el-table-column prop="actual_date" label="实际" width="110" />
          <el-table-column prop="delay_days" label="延误天" width="80" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="responsible_party" label="责任方" width="120" />
          <el-table-column prop="notes" label="备注" min-width="100" show-overflow-tooltip />
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openMilestoneDlg(row)">编辑</el-button>
              <el-button link type="primary" size="small" @click="completeMilestone(row.id)">完成</el-button>
              <el-button link type="warning" size="small" @click="delayMilestone(row.id)">标延误</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span>海运记录</span>
            <el-button size="small" type="primary" @click="openShipRecDlg()">新增记录</el-button>
          </div>
        </template>
        <el-table :data="ws.shipping_records" size="small" stripe>
          <el-table-column prop="origin_factory" label="出厂" width="100" />
          <el-table-column prop="origin_port" label="始发港" width="100" />
          <el-table-column prop="destination_port" label="目的港" width="100" />
          <el-table-column prop="freight_forwarder" label="货代" width="100" />
          <el-table-column prop="etd" label="ETD" width="100" />
          <el-table-column prop="eta" label="ETA" width="100" />
          <el-table-column prop="customs_status" label="清关" width="90" />
          <el-table-column prop="delivery_status" label="交付" width="110" />
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openShipRecDlg(row)">编辑</el-button>
              <el-button link type="primary" size="small" @click="markCustoms(row.id)">清关完成</el-button>
              <el-button link type="primary" size="small" @click="markInbound(row.id)">入仓</el-button>
              <el-button link type="primary" size="small" @click="markFinal(row.id)">最终交付</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never">
        <template #header>订单行</template>
        <el-table :data="ws.order_items" size="small" stripe>
          <el-table-column prop="product_id" label="产品 ID" width="260" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="unit_price" label="单价" width="90" />
        </el-table>
      </el-card>

      <div id="ai-panel">
        <ObjectAiActionsPanel object-type="order" :object-id="orderId" variant="order" :ai-context="aiContext" />
      </div>
      <div id="interaction-panel" class="mt-4">
        <ObjectInteractionsPanel object-type="order" :object-id="orderId" @task-spawned="reload" />
      </div>
      <div id="task-panel" class="mt-4">
        <ObjectTasksPanel object-type="order" :object-id="orderId" />
      </div>
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <ObjectNotesPanel object-type="order" :object-id="orderId" />
        <ObjectTagsPanel object-type="order" :object-id="orderId" />
        <ObjectFilesPanel object-type="order" :object-id="orderId" />
        <div class="lg:col-span-2">
          <ObjectActivityLogPanel object-type="order" :object-id="orderId" />
        </div>
      </div>
    </template>

    <el-dialog v-model="msDlg" title="里程碑" width="480px">
      <el-form label-width="120">
        <el-form-item label="计划日"><el-date-picker v-model="msForm.planned_date" value-format="YYYY-MM-DD" class="w-full" /></el-form-item>
        <el-form-item label="实际日"><el-date-picker v-model="msForm.actual_date" value-format="YYYY-MM-DD" class="w-full" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="msForm.status" clearable filterable class="w-full" placeholder="节点状态">
            <el-option v-for="s in MILESTONE_ROW_STATUSES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="责任方"><el-input v-model="msForm.responsible_party" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="msForm.notes" type="textarea" rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="msDlg = false">取消</el-button>
        <el-button type="primary" @click="saveMilestone">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="srDlg" title="海运记录" width="560px">
      <el-form label-width="140" class="max-h-[70vh] overflow-y-auto">
        <el-form-item label="出厂地"><el-input v-model="srForm.origin_factory" /></el-form-item>
        <el-form-item label="始发港"><el-input v-model="srForm.origin_port" /></el-form-item>
        <el-form-item label="目的港"><el-input v-model="srForm.destination_port" /></el-form-item>
        <el-form-item label="目的仓"><el-input v-model="srForm.destination_warehouse" /></el-form-item>
        <el-form-item label="Incoterm"><el-input v-model="srForm.incoterm" /></el-form-item>
        <el-form-item label="柜型"><el-input v-model="srForm.container_type" /></el-form-item>
        <el-form-item label="外箱尺寸"><el-input v-model="srForm.carton_dimensions" /></el-form-item>
        <el-form-item label="单箱重量"><el-input v-model="srForm.carton_weight" /></el-form-item>
        <el-form-item label="箱数"><el-input v-model="srForm.cartons_count" /></el-form-item>
        <el-form-item label="托盘数"><el-input v-model="srForm.pallet_count" /></el-form-item>
        <el-form-item label="预估 CBM"><el-input v-model="srForm.estimated_cbm" /></el-form-item>
        <el-form-item label="货代"><el-input v-model="srForm.freight_forwarder" /></el-form-item>
        <el-form-item label="订舱日"><el-date-picker v-model="srForm.booking_date" value-format="YYYY-MM-DD" class="w-full" /></el-form-item>
        <el-form-item label="ETD"><el-date-picker v-model="srForm.etd" value-format="YYYY-MM-DD" class="w-full" /></el-form-item>
        <el-form-item label="ETA"><el-date-picker v-model="srForm.eta" value-format="YYYY-MM-DD" class="w-full" /></el-form-item>
        <el-form-item label="实际到港"><el-date-picker v-model="srForm.actual_arrival_date" value-format="YYYY-MM-DD" class="w-full" /></el-form-item>
        <el-form-item label="清关状态"><el-input v-model="srForm.customs_status" /></el-form-item>
        <el-form-item label="交付状态"><el-input v-model="srForm.delivery_status" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="srForm.notes" type="textarea" rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="srDlg = false">取消</el-button>
        <el-button type="primary" @click="saveShipRec">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { http } from '@/api/http'
import { ElMessage } from 'element-plus'
import {
  ObjectActivityLogPanel,
  ObjectAiActionsPanel,
  ObjectFilesPanel,
  ObjectInteractionsPanel,
  ObjectNotesPanel,
  ObjectTagsPanel,
  ObjectTasksPanel,
} from '@/components/object-panels'
import {
  MILESTONE_ROW_STATUSES,
  ORDER_PRODUCTION_STATUSES,
  ORDER_SHIPPING_STATUSES,
} from '@/constants/statusEnums'

const PRODUCTION_PIPELINE = ORDER_PRODUCTION_STATUSES
const SHIPPING_PIPELINE = ORDER_SHIPPING_STATUSES
type OrderWs = Record<string, any>

const route = useRoute()
const orderId = computed(() => String(route.params.orderId))
const loading = ref(false)
const ws = ref<OrderWs | null>(null)
const customerEmailPreview = ref('')

const msDlg = ref(false)
const editingMsId = ref<string | null>(null)
const msForm = reactive({
  planned_date: null as string | null,
  actual_date: null as string | null,
  status: '',
  responsible_party: '',
  notes: '',
})

const srDlg = ref(false)
const editingSrId = ref<string | null>(null)
const srForm = reactive({
  origin_factory: '',
  origin_port: '',
  destination_port: '',
  destination_warehouse: '',
  incoterm: '',
  container_type: '',
  carton_dimensions: '',
  carton_weight: '',
  cartons_count: '',
  pallet_count: '',
  estimated_cbm: '',
  freight_forwarder: '',
  booking_date: null as string | null,
  etd: null as string | null,
  eta: null as string | null,
  actual_arrival_date: null as string | null,
  customs_status: '',
  delivery_status: '',
  notes: '',
})

const aiContext = computed(() => {
  const w = ws.value
  if (!w?.order) return {}
  const o = w.order
  return {
    order_number: o.order_number,
    production_status: o.production_status,
    shipping_status: o.shipping_status,
    risk_level: o.risk_level,
    target_delivery_date: o.target_delivery_date,
    order_date: o.order_date,
    milestones_json: JSON.stringify(w.production_milestones ?? []),
    shipping_records_json: JSON.stringify(w.shipping_records ?? []),
    risk_panel_json: JSON.stringify(w.risk_panel ?? {}),
    company_json: JSON.stringify(w.company ?? {}),
    contact_json: JSON.stringify(w.contact ?? {}),
    lead_json: JSON.stringify(w.lead ?? {}),
    rfq_json: JSON.stringify(w.rfq ?? {}),
    partner_json: JSON.stringify(w.manufacturing_partner ?? {}),
  }
})

async function reload() {
  loading.value = true
  try {
    const { data } = await http.get<OrderWs>(`/orders/${orderId.value}/workspace`)
    ws.value = data
  } finally {
    loading.value = false
  }
}

async function setProductionStatus(st: string) {
  await http.post(`/orders/${orderId.value}/production-status`, { production_status: st })
  ElMessage.success('生产状态已更新')
  reload()
}

async function setShippingStatus(st: string) {
  await http.post(`/orders/${orderId.value}/shipping-status`, { shipping_status: st })
  ElMessage.success('海运状态已更新')
  reload()
}

async function generateMilestones(force: boolean) {
  await http.post(`/orders/${orderId.value}/generate-milestones`, {}, { params: { force } })
  ElMessage.success(force ? '已重建里程碑' : '已生成里程碑')
  reload()
}

function openMilestoneDlg(row: Record<string, unknown>) {
  editingMsId.value = String(row.id)
  msForm.planned_date = (row.planned_date as string) || null
  msForm.actual_date = (row.actual_date as string) || null
  msForm.status = (row.status as string) || ''
  msForm.responsible_party = (row.responsible_party as string) || ''
  msForm.notes = (row.notes as string) || ''
  msDlg.value = true
}

async function saveMilestone() {
  if (!editingMsId.value) return
  await http.put(`/orders/${orderId.value}/milestones/${editingMsId.value}`, { ...msForm })
  ElMessage.success('里程碑已更新')
  msDlg.value = false
  reload()
}

async function completeMilestone(id: string) {
  await http.post(`/orders/${orderId.value}/milestones/${id}/complete`)
  ElMessage.success('已标记完成')
  reload()
}

async function delayMilestone(id: string) {
  await http.post(`/orders/${orderId.value}/milestones/${id}/delayed`)
  ElMessage.success('已标记延误')
  reload()
}

async function genCustomerUpdateEmail() {
  const { data } = await http.post<{ text?: string }>(`/orders/${orderId.value}/customer-update-email`, {
    context: aiContext.value,
  })
  customerEmailPreview.value = data.text || ''
  ElMessage.success('已生成草稿')
}

function openShipRecDlg(row?: Record<string, unknown>) {
  if (row) {
    editingSrId.value = String(row.id)
    Object.assign(srForm, {
      origin_factory: row.origin_factory || '',
      origin_port: row.origin_port || '',
      destination_port: row.destination_port || '',
      destination_warehouse: row.destination_warehouse || '',
      incoterm: row.incoterm || '',
      container_type: row.container_type || '',
      carton_dimensions: row.carton_dimensions || '',
      carton_weight: row.carton_weight || '',
      cartons_count: row.cartons_count != null ? String(row.cartons_count) : '',
      pallet_count: row.pallet_count != null ? String(row.pallet_count) : '',
      estimated_cbm: row.estimated_cbm != null ? String(row.estimated_cbm) : '',
      freight_forwarder: row.freight_forwarder || '',
      booking_date: row.booking_date || null,
      etd: row.etd || null,
      eta: row.eta || null,
      actual_arrival_date: row.actual_arrival_date || null,
      customs_status: row.customs_status || '',
      delivery_status: row.delivery_status || '',
      notes: row.notes || '',
    })
  } else {
    editingSrId.value = null
    Object.assign(srForm, {
      origin_factory: '',
      origin_port: '',
      destination_port: '',
      destination_warehouse: '',
      incoterm: '',
      container_type: '',
      carton_dimensions: '',
      carton_weight: '',
      cartons_count: '',
      pallet_count: '',
      estimated_cbm: '',
      freight_forwarder: '',
      booking_date: null,
      etd: null,
      eta: null,
      actual_arrival_date: null,
      customs_status: '',
      delivery_status: '',
      notes: '',
    })
  }
  srDlg.value = true
}

async function saveShipRec() {
  const body: Record<string, unknown> = {
    origin_factory: srForm.origin_factory || null,
    origin_port: srForm.origin_port || null,
    destination_port: srForm.destination_port || null,
    destination_warehouse: srForm.destination_warehouse || null,
    incoterm: srForm.incoterm || null,
    container_type: srForm.container_type || null,
    carton_dimensions: srForm.carton_dimensions || null,
    carton_weight: srForm.carton_weight || null,
    freight_forwarder: srForm.freight_forwarder || null,
    booking_date: srForm.booking_date,
    etd: srForm.etd,
    eta: srForm.eta,
    actual_arrival_date: srForm.actual_arrival_date,
    customs_status: srForm.customs_status || null,
    delivery_status: srForm.delivery_status || null,
    notes: srForm.notes || null,
  }
  ;['cartons_count', 'pallet_count', 'estimated_cbm'].forEach((k) => {
    const raw = srForm[k as keyof typeof srForm] as string
    if (raw && raw.trim()) {
      const n = Number(raw)
      body[k] = Number.isFinite(n) ? n : null
    } else body[k] = null
  })
  if (editingSrId.value) {
    await http.put(`/orders/${orderId.value}/shipping-records/${editingSrId.value}`, body)
    ElMessage.success('记录已更新')
  } else {
    await http.post(`/orders/${orderId.value}/shipping-records`, body)
    ElMessage.success('已添加记录')
  }
  srDlg.value = false
  reload()
}

async function markCustoms(id: string) {
  await http.post(`/orders/${orderId.value}/shipping-records/${id}/customs-cleared`)
  ElMessage.success('已更新清关')
  reload()
}

async function markInbound(id: string) {
  await http.post(`/orders/${orderId.value}/shipping-records/${id}/warehouse-inbound`)
  ElMessage.success('已标记入仓')
  reload()
}

async function markFinal(id: string) {
  await http.post(`/orders/${orderId.value}/shipping-records/${id}/final-delivered`)
  ElMessage.success('已标记交付')
  reload()
}

reload()
</script>
