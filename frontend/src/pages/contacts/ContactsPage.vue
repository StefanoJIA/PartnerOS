<template>
  <div>
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-semibold text-slate-800">Contacts</h2>
      <el-button type="primary" @click="dialog = true">新建</el-button>
    </div>

    <el-form :inline="true" class="mb-4 flex flex-wrap gap-2">
      <el-form-item label="搜索">
        <el-input v-model="q" placeholder="姓名 / 邮箱 / 公司" clearable class="w-48" @keyup.enter="load" />
      </el-form-item>
      <el-form-item label="公司 ID">
        <el-input v-model="filters.company_id" placeholder="UUID" clearable class="w-56" />
      </el-form-item>
      <el-form-item label="职位">
        <el-input v-model="filters.title" clearable class="w-32" />
      </el-form-item>
      <el-form-item label="类型">
        <el-input v-model="filters.contact_type" clearable class="w-28" />
      </el-form-item>
      <el-form-item label="决策层">
        <el-input v-model="filters.decision_maker_level" clearable class="w-28" />
      </el-form-item>
      <el-form-item label="状态">
        <el-input v-model="filters.status" clearable class="w-24" />
      </el-form-item>
      <el-form-item label="有邮箱">
        <el-select v-model="filters.has_email" clearable placeholder="任意" class="w-24">
          <el-option label="是" :value="true" />
          <el-option label="否" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item label="有 LinkedIn">
        <el-select v-model="filters.has_linkedin" clearable placeholder="任意" class="w-24">
          <el-option label="是" :value="true" />
          <el-option label="否" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="load">筛选</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="rows" stripe v-loading="loading">
      <el-table-column label="姓名" min-width="140">
        <template #default="{ row }">
          <router-link
            class="text-blue-600 hover:underline"
            :to="{ name: 'contact-detail', params: { contactId: row.id } }"
          >
            {{ row.first_name }} {{ row.last_name }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="company_name" label="公司" min-width="160" />
      <el-table-column prop="title" label="职位" width="140" />
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="phone" label="电话" width="120" />
      <el-table-column label="LinkedIn" width="90">
        <template #default="{ row }">
          <a v-if="row.linkedin_url" :href="String(row.linkedin_url)" target="_blank" rel="noreferrer" class="text-blue-600">打开</a>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column prop="contact_type" label="类型" width="100" />
      <el-table-column prop="decision_maker_level" label="决策" width="100" />
      <el-table-column prop="last_contacted_at" label="上次联系" width="120" />
      <el-table-column prop="next_follow_up_at" label="下次跟进" width="120" />
      <el-table-column prop="status" label="状态" width="90" />
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

    <el-dialog v-model="dialog" title="新建联系人" width="520px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="名"><el-input v-model="form.first_name" /></el-form-item>
        <el-form-item label="姓"><el-input v-model="form.last_name" /></el-form-item>
        <el-form-item label="公司 ID (UUID)"><el-input v-model="form.company_id" /></el-form-item>
        <el-form-item label="职位"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
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

const rows = ref<Record<string, unknown>[]>([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const q = ref('')
const loading = ref(false)
const dialog = ref(false)

const filters = reactive({
  company_id: '',
  title: '',
  contact_type: '',
  decision_maker_level: '',
  status: '',
  has_email: undefined as boolean | undefined,
  has_linkedin: undefined as boolean | undefined,
})

const form = reactive({
  first_name: '',
  last_name: '',
  company_id: '',
  title: '',
  email: '',
})

async function load() {
  loading.value = true
  try {
    const { data } = await http.get('/contacts', {
      params: {
        page: page.value,
        limit: limit.value,
        q: q.value || undefined,
        company_id: filters.company_id || undefined,
        title: filters.title || undefined,
        contact_type: filters.contact_type || undefined,
        decision_maker_level: filters.decision_maker_level || undefined,
        status: filters.status || undefined,
        has_email: filters.has_email,
        has_linkedin: filters.has_linkedin,
      },
    })
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function save() {
  await http.post('/contacts', form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

onMounted(load)
</script>
