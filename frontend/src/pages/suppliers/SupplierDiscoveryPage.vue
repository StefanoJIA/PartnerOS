<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="mb-1 text-xl font-semibold text-slate-800">供应商发现与资质</h2>
        <p class="text-sm text-slate-500">人工录入、CSV 导入与评估 — 无自动联系、承诺或激活。</p>
      </div>
      <div class="flex gap-2">
        <el-upload :show-file-list="false" accept=".csv" :http-request="importCsv">
          <el-button type="primary" plain>CSV 导入</el-button>
        </el-upload>
        <el-button @click="showCreate = true">手动录入</el-button>
      </div>
    </div>

    <el-table :data="rows" stripe v-loading="loading">
      <el-table-column prop="company_name" label="公司" min-width="180" />
      <el-table-column prop="brand_name" label="品牌" width="120" />
      <el-table-column prop="country" label="国家" width="90" />
      <el-table-column label="状态" width="130">
        <template #default="{ row }">{{ statusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column prop="risk_level" label="风险" width="80" />
      <el-table-column prop="doc_completeness_pct" label="资料完整度" width="100" />
      <el-table-column prop="data_source" label="来源" width="90" />
      <el-table-column prop="source_review_status" label="审核" width="90" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button v-if="row.status === 'qualified'" size="small" link type="primary" @click="activate(row)">
            激活为 Partner
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      class="mt-4"
      background
      layout="prev, pager, next"
      :total="total"
      v-model:current-page="page"
      :page-size="limit"
      @current-change="load"
    />

    <el-dialog v-model="showCreate" title="录入供应商发现" width="520px">
      <el-form label-width="100px">
        <el-form-item label="公司名"><el-input v-model="form.company_name" /></el-form-item>
        <el-form-item label="国家"><el-input v-model="form.country" /></el-form-item>
        <el-form-item label="来源 URL"><el-input v-model="form.source_url" /></el-form-item>
        <el-form-item label="工厂地址"><el-input v-model="form.factory_address" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createRecord">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '@/api/http'

const STATUS_LABELS: Record<string, string> = {
  discovered: '已发现',
  contacted: '已联系',
  information_requested: '资料请求中',
  evaluating: '评估中',
  sample_requested: '样品已请求',
  sample_received: '样品已收',
  qualified: '已资质通过',
  active: '已激活',
  rejected: '已拒绝',
  paused: '已暂停',
}

function statusLabel(s: string) {
  return STATUS_LABELS[s] || s
}

const rows = ref<unknown[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const loading = ref(false)
const showCreate = ref(false)
const creating = ref(false)
const form = reactive({ company_name: '', country: '', source_url: '', factory_address: '' })

async function load() {
  loading.value = true
  try {
    const { data } = await http.get('/supplier-discovery', { params: { page: page.value, limit: limit.value } })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function createRecord() {
  creating.value = true
  try {
    await http.post('/supplier-discovery', form)
    ElMessage.success('已录入')
    showCreate.value = false
    await load()
  } finally {
    creating.value = false
  }
}

async function importCsv(options: { file: File }) {
  const fd = new FormData()
  fd.append('file', options.file)
  await http.post('/supplier-discovery/import-csv', fd)
  ElMessage.success('CSV 导入完成')
  await load()
}

async function activate(row: { id: string }) {
  await http.post(`/supplier-discovery/${row.id}/activate-partner`)
  ElMessage.success('已手动激活为 Partner')
  await load()
}

onMounted(load)
</script>
