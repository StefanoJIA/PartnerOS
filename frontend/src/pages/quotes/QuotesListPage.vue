<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchQuotes, type QuoteSummary } from '@/api/quotes'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const items = ref<QuoteSummary[]>([])
const statusFilter = ref('')

const SAFETY =
  'Quote records are manually prepared. intelliOffice does not send quotes automatically, does not promise inventory, certifications, or lead times.'

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchQuotes({ status: statusFilter.value || undefined })
    items.value = data.items
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load quotes'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <h1>Customer Quotes</h1>
    <el-alert type="warning" :closable="false" show-icon title="Safety" :description="SAFETY" class="mb" />

    <div class="toolbar">
      <el-select v-model="statusFilter" placeholder="Status" clearable style="width: 200px" @change="load">
        <el-option label="Internal Review" value="internal_review" />
        <el-option label="Ready to Send" value="ready_to_send" />
        <el-option label="Sent" value="sent" />
        <el-option label="Revised" value="revised" />
        <el-option label="Expired" value="expired" />
      </el-select>
      <el-button type="primary" @click="router.push({ name: 'quote-new' })">New Quote</el-button>
    </div>

    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />
    <div v-if="loading" v-loading="true" style="min-height: 120px" />
    <el-table v-else :data="items" stripe @row-click="(row: QuoteSummary) => router.push({ name: 'quote-detail', params: { id: row.id } })">
      <el-table-column prop="quote_number" label="Quote #" width="140" />
      <el-table-column prop="bill_to_company" label="Company" />
      <el-table-column prop="status" label="Status" width="140" />
      <el-table-column prop="grand_total" label="Total" width="120">
        <template #default="{ row }">{{ row.currency }} {{ row.grand_total }}</template>
      </el-table-column>
      <el-table-column prop="valid_until" label="Valid Until" width="120" />
    </el-table>
  </div>
</template>

<style scoped>
.page { padding: 16px; }
.mb { margin-bottom: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }
</style>
