<template>
  <div v-loading="loading" class="space-y-4">
    <el-button link type="primary" @click="$router.push({ name: 'samples' })">← 样品列表</el-button>

    <template v-if="ws">
      <el-card shadow="never">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-slate-800">{{ ws.sample.sample_request_number }}</h2>
            <p class="mt-1 text-sm text-slate-600">状态：{{ ws.sample.sample_status }}</p>
            <div class="mt-2 grid gap-1 text-sm text-slate-700 sm:grid-cols-2">
              <div>样品费：{{ ws.sample.sample_cost ?? '—' }} · 运费：{{ ws.sample.shipping_cost ?? '—' }}</div>
              <div>快递：{{ ws.sample.courier || '—' }} · 运单：{{ ws.sample.tracking_number || '—' }}</div>
              <div>发货：{{ ws.sample.shipped_date || '—' }} · 签收：{{ ws.sample.delivered_date || '—' }}</div>
              <div>跟进截止：{{ ws.sample.follow_up_due_date || '—' }}</div>
              <div>转自 RFQ：{{ ws.sample.converted_to_rfq ? '是' : '否' }} · 已转订单：{{ ws.sample.converted_to_order ? '是' : '否' }}</div>
            </div>
            <p v-if="ws.sample.customer_feedback" class="mt-2 whitespace-pre-wrap text-sm text-slate-800">客户反馈：{{ ws.sample.customer_feedback }}</p>
            <p class="mt-1 text-xs text-slate-500">创建于 {{ ws.sample.created_at }} · 更新 {{ ws.sample.updated_at }}</p>
          </div>
          <div class="text-right text-sm text-slate-600 space-y-1">
            <div v-if="ws.company">公司：{{ ws.company.company_name }}</div>
            <div v-if="ws.contact">{{ ws.contact.first_name }} {{ ws.contact.last_name }}</div>
            <div v-if="ws.lead">线索：{{ ws.lead.lead_name }}</div>
            <div v-if="ws.rfq">RFQ：{{ ws.rfq.rfq_number }}</div>
            <div v-if="ws.product">产品：{{ ws.product.product_name }}</div>
            <div v-if="ws.manufacturing_partner">制造伙伴：{{ ws.manufacturing_partner.partner_name }}</div>
          </div>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <el-button v-if="ws.company" size="small" @click="$router.push({ name: 'company-detail', params: { companyId: ws.company.id } })">打开公司</el-button>
          <el-button v-if="ws.contact" size="small" @click="$router.push({ name: 'contact-detail', params: { contactId: ws.contact.id } })">打开联系人</el-button>
          <el-button v-if="ws.lead" size="small" @click="$router.push({ name: 'lead-detail', params: { leadId: ws.lead.id } })">打开线索</el-button>
          <el-button v-if="ws.rfq" size="small" @click="$router.push({ name: 'rfq-detail', params: { rfqId: ws.rfq.id } })">打开 RFQ</el-button>
          <el-button v-if="ws.product" size="small" @click="$router.push({ name: 'product-detail', params: { productId: ws.product.id } })">打开产品</el-button>
          <el-button
            v-if="ws.manufacturing_partner"
            size="small"
            @click="$router.push({ name: 'partner-detail', params: { partnerId: ws.manufacturing_partner.id } })"
          >
            打开制造伙伴
          </el-button>
          <el-button
            v-if="ws.related_order"
            size="small"
            type="primary"
            @click="$router.push({ name: 'order-detail', params: { orderId: ws.related_order.id } })"
          >
            打开订单
          </el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>状态管线</template>
        <div class="flex flex-wrap gap-2">
          <el-button
            v-for="st in SAMPLE_PIPELINE"
            :key="st"
            size="small"
            :type="ws.sample.sample_status === st ? 'primary' : 'default'"
            @click="setStatus(st)"
          >
            {{ st }}
          </el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>快捷动作</template>
        <div class="flex flex-wrap gap-2">
          <el-button size="small" @click="setStatus('Internal Review')">内部评审</el-button>
          <el-button size="small" @click="setStatus('Waiting for Partner')">等待伙伴</el-button>
          <el-button size="small" @click="setStatus('Ready')">就绪待发</el-button>
          <el-button size="small" @click="setStatus('Shipped')">标记已发运</el-button>
          <el-button size="small" @click="setStatus('Delivered')">标记签收</el-button>
          <el-button size="small" @click="openFeedbackDlg()">记录反馈</el-button>
          <el-button size="small" @click="scrollTo('ai-panel')">生成跟进邮件（AI）</el-button>
          <el-button size="small" @click="scrollTo('task-panel')">创建任务</el-button>
          <el-button size="small" @click="scrollTo('interaction-panel')">记录互动</el-button>
          <el-button v-if="!ws.sample.converted_to_order" size="small" type="primary" @click="openConvertDlg()">转为订单</el-button>
          <el-button size="small" @click="setStatus('Closed')">关闭样品</el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>运输信息</template>
        <el-form label-width="120" class="max-w-3xl" @submit.prevent="saveShipping">
          <el-form-item label="承运商"><el-input v-model="shipForm.courier" /></el-form-item>
          <el-form-item label="运单号"><el-input v-model="shipForm.tracking_number" /></el-form-item>
          <el-form-item label="运费"><el-input v-model="shipForm.shipping_cost" placeholder="数字" /></el-form-item>
          <el-form-item label="发货日"><el-date-picker v-model="shipForm.shipped_date" value-format="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="签收日"><el-date-picker v-model="shipForm.delivered_date" value-format="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="目的地"><el-input v-model="shipForm.shipping_destination" type="textarea" rows="2" /></el-form-item>
          <el-form-item label="备注"><el-input v-model="shipForm.notes" type="textarea" rows="2" /></el-form-item>
          <el-form-item><el-button type="primary" native-type="submit">保存运输</el-button></el-form-item>
        </el-form>
      </el-card>

      <el-card shadow="never">
        <template #header>反馈（概要）</template>
        <p class="mb-2 text-sm text-slate-600">详细编辑请使用下方「记录反馈」对话框，或保存此处快速备注。</p>
        <el-button size="small" @click="openFeedbackDlg()">打开反馈表单</el-button>
      </el-card>

      <div id="ai-panel">
        <ObjectAiActionsPanel object-type="sample" :object-id="sampleId" variant="sample" :ai-context="aiContext" />
      </div>
      <div id="interaction-panel" class="mt-4">
        <ObjectInteractionsPanel object-type="sample" :object-id="sampleId" @task-spawned="reload" />
      </div>
      <div id="task-panel" class="mt-4">
        <ObjectTasksPanel object-type="sample" :object-id="sampleId" />
      </div>
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <ObjectNotesPanel object-type="sample" :object-id="sampleId" />
        <ObjectTagsPanel object-type="sample" :object-id="sampleId" />
        <ObjectFilesPanel object-type="sample" :object-id="sampleId" />
        <div class="lg:col-span-2">
          <ObjectActivityLogPanel object-type="sample" :object-id="sampleId" />
        </div>
      </div>
    </template>

    <el-dialog v-model="feedbackDlg" title="记录客户反馈" width="520px" @open="syncFeedbackForm">
      <el-form label-width="120">
        <el-form-item label="反馈内容"><el-input v-model="feedbackForm.customer_feedback" type="textarea" rows="4" /></el-form-item>
        <el-form-item label="反馈日期"><el-date-picker v-model="feedbackForm.feedback_date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="兴趣度"><el-input v-model="feedbackForm.interest_level" /></el-form-item>
        <el-form-item label="下一步"><el-input v-model="feedbackForm.next_action" type="textarea" rows="2" /></el-form-item>
        <el-form-item label="跟进截止"><el-date-picker v-model="feedbackForm.follow_up_due_date" value-format="YYYY-MM-DD" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feedbackDlg = false">取消</el-button>
        <el-button type="primary" @click="saveFeedback">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="convertDlg" title="样品转订单" width="480px">
      <el-form label-width="140">
        <el-form-item label="制造伙伴" required>
          <el-select v-model="convertForm.manufacturing_partner_id" filterable placeholder="选择伙伴" class="w-full">
            <el-option v-for="p in partnerOptions" :key="p.id" :label="p.partner_name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="生成里程碑">
          <el-switch v-model="convertForm.generate_milestones" />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="convertForm.notes" type="textarea" rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="convertDlg = false">取消</el-button>
        <el-button type="primary" @click="doConvert">创建订单</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
import { SAMPLE_STATUSES } from '@/constants/statusEnums'

const SAMPLE_PIPELINE = SAMPLE_STATUSES
type SampleWs = Record<string, any>

const route = useRoute()
const router = useRouter()
const sampleId = computed(() => String(route.params.sampleId))
const loading = ref(false)
const ws = ref<SampleWs | null>(null)

const shipForm = reactive({
  courier: '',
  tracking_number: '',
  shipping_cost: '' as string,
  shipped_date: '' as string | null,
  delivered_date: '' as string | null,
  shipping_destination: '',
  notes: '',
})

const feedbackDlg = ref(false)
const feedbackForm = reactive({
  customer_feedback: '',
  feedback_date: '' as string | null,
  interest_level: '',
  next_action: '',
  follow_up_due_date: '' as string | null,
})

const convertDlg = ref(false)
const convertForm = reactive({
  manufacturing_partner_id: '' as string,
  generate_milestones: false,
  notes: '',
})
const partnerOptions = ref<{ id: string; partner_name: string }[]>([])

const aiContext = computed(() => {
  const w = ws.value
  if (!w?.sample) return {}
  const s = w.sample
  return {
    sample_request_number: s.sample_request_number,
    sample_status: s.sample_status,
    sample_cost: s.sample_cost,
    shipping_cost: s.shipping_cost,
    courier: s.courier,
    tracking_number: s.tracking_number,
    shipped_date: s.shipped_date,
    delivered_date: s.delivered_date,
    customer_feedback: s.customer_feedback,
    interest_level: s.interest_level,
    next_action: s.next_action,
    company_json: JSON.stringify(w.company ?? {}),
    contact_json: JSON.stringify(w.contact ?? {}),
    lead_json: JSON.stringify(w.lead ?? {}),
    rfq_json: JSON.stringify(w.rfq ?? {}),
    product_json: JSON.stringify(w.product ?? {}),
    partner_json: JSON.stringify(w.manufacturing_partner ?? {}),
  }
})

watch(
  () => ws.value,
  (w) => {
    if (!w?.sample) return
    const s = w.sample
    shipForm.courier = s.courier || ''
    shipForm.tracking_number = s.tracking_number || ''
    shipForm.shipping_cost = s.shipping_cost != null ? String(s.shipping_cost) : ''
    shipForm.shipped_date = s.shipped_date || null
    shipForm.delivered_date = s.delivered_date || null
    shipForm.shipping_destination = s.shipping_destination || ''
    shipForm.notes = ''
  },
  { immediate: true },
)

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

async function reload() {
  loading.value = true
  try {
    const { data } = await http.get<SampleWs>(`/samples/${sampleId.value}/workspace`)
    ws.value = data
  } finally {
    loading.value = false
  }
}

async function setStatus(st: string) {
  await http.post(`/samples/${sampleId.value}/status`, { status: st })
  ElMessage.success('状态已更新')
  reload()
}

async function saveShipping() {
  const body: Record<string, unknown> = {
    courier: shipForm.courier || null,
    tracking_number: shipForm.tracking_number || null,
    shipping_destination: shipForm.shipping_destination || null,
    notes: shipForm.notes || null,
    shipped_date: shipForm.shipped_date || null,
    delivered_date: shipForm.delivered_date || null,
  }
  if (shipForm.shipping_cost.trim()) {
    const n = Number(shipForm.shipping_cost)
    body.shipping_cost = Number.isFinite(n) ? n : null
  } else body.shipping_cost = null
  await http.put(`/samples/${sampleId.value}/shipping`, body)
  ElMessage.success('运输信息已保存')
  reload()
}

function openFeedbackDlg() {
  feedbackDlg.value = true
}

function syncFeedbackForm() {
  const s = ws.value?.sample
  if (!s) return
  feedbackForm.customer_feedback = s.customer_feedback || ''
  feedbackForm.feedback_date = s.feedback_date || null
  feedbackForm.interest_level = s.interest_level || ''
  feedbackForm.next_action = s.next_action || ''
  feedbackForm.follow_up_due_date = s.follow_up_due_date || null
}

async function saveFeedback() {
  await http.post(`/samples/${sampleId.value}/feedback`, { ...feedbackForm })
  ElMessage.success('反馈已记录')
  feedbackDlg.value = false
  reload()
}

async function loadPartners() {
  const { data } = await http.get('/manufacturing-partners', { params: { page: 1, limit: 500 } })
  partnerOptions.value = data.items
}

async function openConvertDlg() {
  await loadPartners()
  const def = ws.value?.sample?.manufacturing_partner_id || ws.value?.manufacturing_partner?.id
  convertForm.manufacturing_partner_id = def ? String(def) : ''
  convertForm.generate_milestones = true
  convertForm.notes = ''
  convertDlg.value = true
}

async function doConvert() {
  if (!convertForm.manufacturing_partner_id) {
    ElMessage.warning('请选择制造伙伴')
    return
  }
  const { data } = await http.post(`/samples/${sampleId.value}/convert-to-order`, {
    manufacturing_partner_id: convertForm.manufacturing_partner_id,
    generate_milestones: convertForm.generate_milestones,
    notes: convertForm.notes || null,
  })
  ElMessage.success('已创建订单')
  convertDlg.value = false
  await reload()
  router.push({ name: 'order-detail', params: { orderId: data.id } })
}

reload()
</script>
