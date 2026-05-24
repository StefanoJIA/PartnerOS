<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  exportQuotePdf,
  fetchQuote,
  fetchQuotePdfExports,
  markQuoteReady,
  markQuoteSent,
  quotePdfDownloadUrl,
  type PdfExportRecord,
  type QuoteDetail,
} from '@/api/quotes'

const route = useRoute()
const loading = ref(true)
const error = ref('')
const quote = ref<QuoteDetail | null>(null)
const actionLoading = ref(false)
const pdfExports = ref<PdfExportRecord[]>([])
const pdfLoading = ref(false)
const pdfError = ref('')
const pdfExporting = ref(false)

const SAFETY =
  'Quote records are manually prepared. intelliOffice does not send quotes automatically, does not promise inventory, certifications, or lead times.'

const PDF_SAFETY =
  'Exporting a PDF does not send the quote, promise inventory, confirm certifications, or commit to lead times.'

const warnings = computed(() => quote.value?.warnings ?? [])

async function loadPdfExports() {
  if (!quote.value) return
  pdfLoading.value = true
  pdfError.value = ''
  try {
    const data = await fetchQuotePdfExports(quote.value.id)
    pdfExports.value = data.items
  } catch (e: unknown) {
    pdfError.value = e instanceof Error ? e.message : 'Failed to load PDF exports'
  } finally {
    pdfLoading.value = false
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    quote.value = await fetchQuote(String(route.params.id))
    await loadPdfExports()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load quote'
  } finally {
    loading.value = false
  }
}

async function onExportPdf() {
  if (!quote.value) return
  pdfExporting.value = true
  pdfError.value = ''
  try {
    await exportQuotePdf(quote.value.id)
    await loadPdfExports()
  } catch (e: unknown) {
    pdfError.value = e instanceof Error ? e.message : 'PDF export failed'
  } finally {
    pdfExporting.value = false
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

      <section class="pdf-section mb">
        <h3>Quote PDF Exports</h3>
        <el-alert type="info" :closable="false" show-icon title="PDF Safety" :description="PDF_SAFETY" class="mb" />
        <el-alert v-if="pdfError" type="error" :title="pdfError" show-icon class="mb" />
        <el-button type="primary" :loading="pdfExporting" @click="onExportPdf">Export Customer PDF</el-button>

        <div v-if="pdfLoading" v-loading="true" style="min-height: 80px; margin-top: 16px" />
        <el-empty v-else-if="!pdfExports.length" description="No PDF exports yet" class="mt" />
        <el-table v-else :data="pdfExports" stripe class="mt">
          <el-table-column prop="file_name" label="File" />
          <el-table-column prop="exported_at" label="Exported At" width="200" />
          <el-table-column prop="file_size_bytes" label="Size (bytes)" width="120" />
          <el-table-column label="Download" width="120">
            <template #default="{ row }">
              <el-link
                :href="quotePdfDownloadUrl(quote.id, row.export_id)"
                target="_blank"
                type="primary"
              >
                Download
              </el-link>
            </template>
          </el-table-column>
        </el-table>
      </section>

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
.mt { margin-top: 16px; }
.actions { display: flex; gap: 12px; }
.pdf-section { border-top: 1px solid var(--el-border-color); padding-top: 16px; }
</style>
