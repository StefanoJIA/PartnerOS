<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-xl font-semibold text-slate-800">线索列表</h2>
      <el-button type="primary" @click="dialog = true">新增</el-button>
    </div>
    <el-form :inline="true" class="mb-4 flex flex-wrap gap-2" @submit.prevent="load">
      <el-form-item label="阶段">
        <el-select v-model="listFilters.stage" clearable placeholder="全部" class="w-48" filterable>
          <el-option v-for="s in LEAD_STAGES" :key="s" :label="s" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item label="搜索">
        <el-input v-model="listFilters.q" clearable placeholder="线索名称" class="w-44" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit">筛选</el-button>
      </el-form-item>
    </el-form>
    <el-table :data="rows" stripe v-loading="loading">
      <template #empty>
        <el-empty description="暂无线索" />
      </template>
      <el-table-column label="名称">
        <template #default="{ row }">
          <router-link class="text-blue-600 hover:underline" :to="{ name: 'lead-detail', params: { leadId: row.id } }">
            {{ row.lead_name }}
          </router-link>
        </template>
      </el-table-column>
      <el-table-column prop="current_stage" label="阶段" width="160" />
      <el-table-column prop="priority" label="优先级" width="100" />
      <el-table-column prop="source" label="来源" width="120" />
      <el-table-column prop="next_action_due_date" label="下次跟进" width="120" />
      <el-table-column prop="lead_type" label="类型" width="160" />
    </el-table>
    <el-dialog v-model="dialog" title="新建线索" width="520px">
      <el-form label-position="top">
        <el-form-item label="名称"><el-input v-model="form.lead_name" /></el-form-item>
        <el-form-item label="Company ID (UUID)"><el-input v-model="form.company_id" /></el-form-item>
        <el-form-item label="来源">
          <el-select v-model="form.source" class="w-full" filterable>
            <el-option label="LinkedIn" value="LinkedIn" />
            <el-option label="Email" value="Email" />
            <el-option label="Referral" value="Referral" />
            <el-option label="Website" value="Website" />
            <el-option label="Other" value="Other" />
          </el-select>
        </el-form-item>
        <el-form-item label="线索类型">
          <el-select v-model="form.lead_type" class="w-full" filterable>
            <el-option label="RFQ Opportunity" value="RFQ Opportunity" />
            <el-option label="Channel Lead" value="Channel Lead" />
            <el-option label="Project Buyer" value="Project Buyer" />
            <el-option label="Sample Opportunity" value="Sample Opportunity" />
          </el-select>
        </el-form-item>
        <el-form-item label="阶段">
          <el-select v-model="form.current_stage" class="w-full" filterable>
            <el-option v-for="s in LEAD_STAGES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
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
import { LEAD_STAGES } from '@/constants/statusEnums'
import { ElMessage } from 'element-plus'

const rows = ref<unknown[]>([])
const loading = ref(false)
const dialog = ref(false)
const listFilters = reactive({
  stage: '' as string,
  q: '' as string,
})
const form = reactive({
  lead_name: '',
  company_id: '',
  source: 'LinkedIn',
  lead_type: 'Channel Lead',
  current_stage: 'New',
})

async function load() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (listFilters.stage) params.stage = listFilters.stage
    if (listFilters.q.trim()) params.q = listFilters.q.trim()
    const { data } = await http.get('/leads', { params })
    rows.value = data.items
  } finally {
    loading.value = false
  }
}

async function save() {
  await http.post('/leads', form)
  ElMessage.success('已保存')
  dialog.value = false
  await load()
}

onMounted(load)
</script>
