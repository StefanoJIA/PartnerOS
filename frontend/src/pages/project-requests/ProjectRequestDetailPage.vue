<template>
  <div v-loading="loading">
    <div v-if="row" class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-xl font-semibold text-slate-800">{{ row.request_reference }}</h2>
          <p class="text-sm text-slate-500">{{ statusLabel(row.status) }} · {{ row.source }}</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <el-button @click="router.push({ name: 'project-requests' })">返回列表</el-button>
          <el-button type="primary" :loading="contractLoading" @click="generateContract">生成 Quote Input Contract</el-button>
          <el-button
            v-if="row.quote_input_contract || contractText"
            type="success"
            @click="router.push({ name: 'quote-new', query: { projectRequestId: row.id } })"
          >
            从 QIC 创建报价
          </el-button>
          <el-button :loading="signalLoading" @click="promoteSignal">提交 Market Response 审核</el-button>
        </div>
      </div>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>客户与需求</template>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="客户">{{ row.customer_name || '—' }}</el-descriptions-item>
              <el-descriptions-item label="邮箱">{{ row.customer_email || '—' }}</el-descriptions-item>
              <el-descriptions-item label="公司">{{ row.company_name || row.company_name_text || '—' }}</el-descriptions-item>
              <el-descriptions-item label="产品意向">{{ row.product_interest || '—' }}</el-descriptions-item>
              <el-descriptions-item label="SKU">{{ row.sku || '—' }}</el-descriptions-item>
              <el-descriptions-item label="数量">{{ qtyLabel }}</el-descriptions-item>
              <el-descriptions-item label="交付地区">{{ row.delivery_region || '—' }}</el-descriptions-item>
              <el-descriptions-item label="项目场景">{{ row.project_scenario || '—' }}</el-descriptions-item>
              <el-descriptions-item label="完整度">{{ row.completeness_pct ?? '—' }}%</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>运营操作</template>
            <el-form label-width="100px" class="max-w-lg">
              <el-form-item label="状态">
                <el-select v-model="edit.status" class="w-full">
                  <el-option v-for="s in STATUSES" :key="s" :label="statusLabel(s)" :value="s" />
                </el-select>
              </el-form-item>
              <el-form-item label="优先级">
                <el-select v-model="edit.priority" class="w-full">
                  <el-option v-for="p in PRIORITIES" :key="p" :label="p" :value="p" />
                </el-select>
              </el-form-item>
              <el-form-item label="SKU">
                <el-input v-model="edit.sku" />
              </el-form-item>
              <el-form-item label="备注">
                <el-input v-model="edit.operator_notes" type="textarea" :rows="3" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="saving" @click="save">保存</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>

      <el-card v-if="row.fit_summary" shadow="never">
        <template #header>
          产品能力匹配 · {{ row.fit_summary.overall_status }}
          <span v-if="row.fit_summary.partner_pending" class="ml-2 text-amber-600">(伙伴 catalog pending)</span>
        </template>
        <p class="mb-3 text-xs text-slate-500">{{ row.fit_summary.disclaimer }}</p>
        <el-table :data="row.fit_summary.matches || []" size="small" stripe>
          <el-table-column prop="label" label="维度" min-width="180" />
          <el-table-column prop="match_status" label="匹配" width="120" />
          <el-table-column prop="evidence_source" label="证据来源" min-width="160" />
          <el-table-column prop="gap_notes" label="缺口" min-width="200" show-overflow-tooltip />
          <el-table-column label="工程评审" width="90">
            <template #default="{ row: m }">{{ m.engineering_review_required ? '是' : '否' }}</template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <span>多供应商候选比对</span>
            <el-button size="small" :loading="candidatesLoading" @click="refreshCandidates">刷新候选</el-button>
          </div>
        </template>
        <p class="mb-3 text-xs text-slate-500">legacy / pending / benchmark 不可自动进入正式报价。</p>
        <el-table :data="candidates" size="small" stripe>
          <el-table-column prop="display_name" label="候选" min-width="200" />
          <el-table-column prop="candidate_source_type" label="来源" width="100" />
          <el-table-column prop="overall_fit_status" label="总体" width="100" />
          <el-table-column prop="candidate_role" label="角色" width="120" />
          <el-table-column label="可报价" width="80">
            <template #default="{ row: c }">{{ c.eligible_for_formal_quote ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="{ row: c }">
              <el-button
                v-if="c.eligible_for_formal_quote"
                size="small"
                type="primary"
                link
                @click="selectCandidate(c)"
              >
                选为主候选
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="contractText" shadow="never">
        <template #header>Quote Input Contract</template>
        <pre class="whitespace-pre-wrap text-sm text-slate-700">{{ contractText }}</pre>
      </el-card>

      <el-card v-if="row.market_signal_draft" shadow="never">
        <template #header>Market Response 信号草稿（需人工审核）</template>
        <pre class="whitespace-pre-wrap text-xs text-slate-600">{{ JSON.stringify(row.market_signal_draft, null, 2) }}</pre>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { http } from '@/api/http'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const contractLoading = ref(false)
const signalLoading = ref(false)
const row = ref<Record<string, any> | null>(null)
const contractText = ref('')
const candidates = ref<Record<string, unknown>[]>([])
const candidatesLoading = ref(false)

const STATUSES = ['submitted', 'triage', 'needs_information', 'quote_ready', 'converted', 'declined']
const PRIORITIES = ['low', 'normal', 'high', 'urgent']

const STATUS_LABELS: Record<string, string> = {
  submitted: '已提交',
  triage: '分拣中',
  needs_information: '待补充资料',
  quote_ready: '可报价',
  converted: '已转化',
  declined: '已拒绝',
}

function statusLabel(s: string) {
  return STATUS_LABELS[s] || s
}

const edit = reactive({
  status: 'submitted',
  priority: 'normal',
  sku: '',
  operator_notes: '',
})

const qtyLabel = computed(() => {
  if (!row.value) return '—'
  const min = row.value.quantity_min
  const max = row.value.quantity_max
  if (min && max && min !== max) return `${min}–${max}`
  if (min) return String(min)
  return '—'
})

async function loadCandidates() {
  const { data } = await http.get(`/project-requests/${route.params.requestId}/candidates`)
  candidates.value = data
}

async function refreshCandidates() {
  candidatesLoading.value = true
  try {
    const { data } = await http.post(`/project-requests/${route.params.requestId}/refresh-candidates`)
    candidates.value = data
    ElMessage.success('候选已刷新')
  } finally {
    candidatesLoading.value = false
  }
}

async function selectCandidate(c: Record<string, unknown>) {
  await http.post(`/project-requests/${route.params.requestId}/candidates/${c.id}/decision`, {
    decision: 'selected',
    reason: 'Operator selected from multi-supplier compare',
  })
  ElMessage.success('已记录选择')
  await loadCandidates()
}

async function load() {
  loading.value = true
  try {
    const { data } = await http.get(`/project-requests/${route.params.requestId}`)
    row.value = data
    edit.status = data.status
    edit.priority = data.priority
    edit.sku = data.sku || ''
    edit.operator_notes = data.operator_notes || ''
    await loadCandidates()
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const { data } = await http.patch(`/project-requests/${route.params.requestId}`, {
      status: edit.status,
      priority: edit.priority,
      sku: edit.sku || null,
      operator_notes: edit.operator_notes || null,
    })
    row.value = data
    ElMessage.success('已保存')
  } finally {
    saving.value = false
  }
}

async function generateContract() {
  contractLoading.value = true
  try {
    const { data } = await http.post(`/project-requests/${route.params.requestId}/quote-input-contract`)
    contractText.value = data.summary_text || JSON.stringify(data.quote_input_contract, null, 2)
    ElMessage.success('Quote Input Contract 已生成')
  } finally {
    contractLoading.value = false
  }
}

async function promoteSignal() {
  signalLoading.value = true
  try {
    await http.post(`/project-requests/${route.params.requestId}/promote-market-signal`)
    ElMessage.success('已提交 Market Response 审核队列')
    await load()
  } finally {
    signalLoading.value = false
  }
}

onMounted(load)
</script>
