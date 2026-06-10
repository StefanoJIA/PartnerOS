<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-800">公司</h2>
      <el-button type="primary" @click="openDialog">新增</el-button>
    </div>
    <el-input v-model="q" placeholder="搜索" class="mb-4 max-w-md" clearable @keyup.enter="load" />
    <el-table :data="rows" stripe v-loading="loading">
      <template #empty>
        <el-empty description="暂无公司，可点击新增" />
      </template>
      <el-table-column label="名称">
        <template #default="{ row }">
          <router-link
            class="text-blue-600 hover:underline"
            :to="{ name: 'company-detail', params: { companyId: row.id } }"
          >
            {{ row.company_name }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="company_type" label="类型" width="160" />
      <el-table-column prop="city" label="城市" width="120" />
      <el-table-column prop="state" label="州/省" width="80" />
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

    <el-dialog v-model="dialog" title="新建公司" width="520px">
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model="form.company_name" /></el-form-item>
        <el-form-item label="类型"><el-input v-model="form.company_type" placeholder="例如 Office Furniture Dealer" /></el-form-item>
        <el-form-item label="城市"><el-input v-model="form.city" /></el-form-item>
        <el-form-item label="州/省"><el-input v-model="form.state" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { http } from '@/api/http'
import { ElMessage } from 'element-plus'

const rows = ref<unknown[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const q = ref('')
const loading = ref(false)
const dialog = ref(false)
const form = reactive({
  company_name: '',
  company_type: 'Office Furniture Dealer',
  city: '',
  state: '',
  country: 'United States',
})

async function load() {
  loading.value = true
  try {
    const { data } = await http.get('/companies', { params: { page: page.value, limit: limit.value, q: q.value || undefined } })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openDialog() {
  dialog.value = true
}

async function save() {
  await http.post('/companies', form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

onMounted(load)
</script>
