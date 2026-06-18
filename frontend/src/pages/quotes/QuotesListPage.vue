<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deleteQuote, fetchQuotes, type QuoteSummary } from '@/api/quotes'
import { QUOTE_STATUS_LABELS, zhLabel } from '@/copy/zhCN'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const items = ref<QuoteSummary[]>([])
const statusFilter = ref('')
const deletingId = ref('')

const SAFETY =
  '报价记录由人工准备。intelliOffice 不会自动发送报价，也不会承诺库存、认证或交期。'

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchQuotes({ status: statusFilter.value || undefined })
    items.value = data.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '报价列表加载失败'
  } finally {
    loading.value = false
  }
}

function canDeleteQuote(row: QuoteSummary) {
  return ['internal_review', 'ready_to_send', 'revised', 'expired'].includes(row.status)
}

async function removeQuote(row: QuoteSummary) {
  if (!canDeleteQuote(row) || deletingId.value) return
  const confirmed = window.confirm(`删除报价 ${row.quote_number}？此操作会归档该报价并从列表中移除。`)
  if (!confirmed) return

  deletingId.value = row.id
  error.value = ''
  try {
    await deleteQuote(row.id)
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '删除报价失败'
  } finally {
    deletingId.value = ''
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <h1>客户报价单</h1>
    <el-alert type="warning" :closable="false" show-icon title="安全边界" :description="SAFETY" class="mb" />

    <div class="toolbar">
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 200px" @change="load">
        <el-option label="内部审核" value="internal_review" />
        <el-option label="待发送" value="ready_to_send" />
        <el-option label="已发送" value="sent" />
        <el-option label="已修订" value="revised" />
        <el-option label="已过期" value="expired" />
      </el-select>
      <el-button type="primary" @click="router.push({ name: 'quote-new' })">新建报价</el-button>
    </div>

    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />
    <div v-if="loading" v-loading="true" style="min-height: 120px" />
    <el-table v-else :data="items" stripe @row-click="(row: QuoteSummary) => router.push({ name: 'quote-detail', params: { id: row.id } })">
      <el-table-column prop="quote_number" label="报价号" width="140" />
      <el-table-column prop="bill_to_company" label="公司" />
      <el-table-column label="状态" width="140">
        <template #default="{ row }">{{ zhLabel(QUOTE_STATUS_LABELS, row.status) }}</template>
      </el-table-column>
      <el-table-column prop="grand_total" label="参考金额" width="120">
        <template #default="{ row }">{{ row.currency }} {{ row.grand_total }}</template>
      </el-table-column>
      <el-table-column prop="valid_until" label="有效期至" width="120" />
      <el-table-column label="操作" width="120" align="right">
        <template #default="{ row }">
          <el-button
            size="small"
            type="danger"
            plain
            :disabled="!canDeleteQuote(row)"
            :loading="deletingId === row.id"
            @click.stop="removeQuote(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.page { padding: 16px; }
.mb { margin-bottom: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
</style>
