<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { fetchQuote, markQuoteReady, markQuoteSent, type QuoteDetail } from '@/api/quotes'

const route = useRoute()
const loading = ref(true)
const error = ref('')
const quote = ref<QuoteDetail | null>(null)
const actionLoading = ref(false)

const SAFETY =
  'Quote records are manually prepared. intelliOffice does not send quotes automatically, does not promise inventory, certifications, or lead times.'

const warnings = computed(() => quote.value?.warnings ?? [])

async function load() {
  loading.value = true
  error.value = ''
  try {
    quote.value = await fetchQuote(String(route.params.id))
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load quote'
  } finally {
    loading.value = false
  }
}

async function onMarkReady() {
  if (!quote.value) return
  actionLoading.value = true
  try {
    quote.value = await markQuoteReady(quote.value.id)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Mark ready failed'
  } finally {
    actionLoading.value = false
  }
}

async function onMarkSent() {
  if (!quote.value) return
  actionLoading.value = true
  try {
    quote.value = await markQuoteSent(quote.value.id, 'manual_email')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Mark sent failed'
  } finally {
    actionLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <el-button link @click="$router.push({ name: 'quotes' })">← Back to Quotes</el-button>
    <h1 v-if="quote">{{ quote.quote_number }}</h1>
    <el-alert type="warning" :closable="false" show-icon title="Safety" :description="SAFETY" class="mb" />
    <el-alert v-if="error" type="error" :title="error" show-icon class="mb" />
    <el-alert v-for="(w, i) in warnings" :key="i" type="warning" :title="w" show-icon class="mb" />

    <div v-if="loading" v-loading="true" style="min-height: 160px" />
    <template v-else-if="quote">
      <el-descriptions :column="2" border class="mb">
        <el-descriptions-item label="Status">{{ quote.status }}</el-descriptions-item>
        <el-descriptions-item label="Valid Until">{{ quote.valid_until }}</el-descriptions-item>
        <el-descriptions-item label="Payment Terms">{{ quote.payment_terms }}</el-descriptions-item>
        <el-descriptions-item label="Shipping Terms">{{ quote.shipping_terms }}</el-descriptions-item>
        <el-descriptions-item label="Subtotal">{{ quote.currency }} {{ quote.subtotal }}</el-descriptions-item>
        <el-descriptions-item label="Grand Total">{{ quote.currency }} {{ quote.grand_total }}</el-descriptions-item>
      </el-descriptions>

      <h3>Line Items</h3>
      <el-table :data="quote.line_items" stripe class="mb">
        <el-table-column prop="line_number" label="#" width="50" />
        <el-table-column prop="product_name" label="Product" />
        <el-table-column prop="quantity" label="Qty" width="80" />
        <el-table-column prop="final_unit_price" label="Unit Price" width="120" />
        <el-table-column prop="total_price" label="Total" width="120" />
        <el-table-column prop="pricing_source" label="Source" width="140" />
      </el-table>

      <div class="actions">
        <el-button
          v-if="quote.status === 'internal_review'"
          type="primary"
          :loading="actionLoading"
          @click="onMarkReady"
        >
          Mark Ready to Send
        </el-button>
        <el-button
          v-if="quote.status === 'ready_to_send'"
          type="success"
          :loading="actionLoading"
          @click="onMarkSent"
        >
          Mark as Sent (manual)
        </el-button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page { padding: 16px; }
.mb { margin-bottom: 16px; }
.actions { display: flex; gap: 12px; }
</style>
