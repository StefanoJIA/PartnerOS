<template>
  <div class="mx-auto max-w-7xl">
    <el-card shadow="never">
      <template #header>
        <div>
          <h1 class="text-xl font-semibold text-slate-800">Lead Intake</h1>
          <p class="mt-1 text-sm text-slate-500">
            Import and review leads before adding them to the manual outreach queue.
          </p>
        </div>
      </template>

      <el-alert type="info" :closable="false" show-icon class="mb-3" :title="LEAD_INTAKE_SAFETY_NOTICE" />
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        class="mb-4"
        title="Privacy & safety"
        :description="privacyBullets"
      />

      <!-- Template -->
      <section class="mb-6">
        <h2 class="mb-2 text-sm font-semibold text-slate-700">CSV template</h2>
        <p class="mb-2 text-sm text-slate-500">
          Use the template to prepare company, contact, website, notes, and source fields.
        </p>
        <el-button :loading="templateLoading" @click="downloadTemplate">Download CSV Template</el-button>
      </section>

      <!-- Input -->
      <section class="mb-6">
        <h2 class="mb-2 text-sm font-semibold text-slate-700">Input</h2>
        <el-tabs v-model="inputTab">
          <el-tab-pane label="Paste CSV" name="paste">
            <el-input
              v-model="csvText"
              type="textarea"
              :rows="10"
              placeholder="Paste CSV content here (include header row)..."
              class="font-mono text-xs"
            />
          </el-tab-pane>
          <el-tab-pane label="Upload CSV" name="upload">
            <el-upload
              drag
              :auto-upload="false"
              :show-file-list="false"
              accept=".csv,text/csv"
              :on-change="onFileSelected"
            >
              <div class="py-6 text-sm text-slate-500">
                Drop a CSV file here or click to browse
              </div>
            </el-upload>
            <p v-if="uploadFileName" class="mt-2 text-xs text-slate-500">Loaded: {{ uploadFileName }}</p>
          </el-tab-pane>
        </el-tabs>
        <div class="mt-3 flex gap-2">
          <el-button type="primary" :loading="previewLoading" :disabled="!csvText.trim()" @click="runPreview">
            Preview
          </el-button>
          <el-button @click="clearAll">Clear</el-button>
        </div>
        <el-alert v-if="previewError" type="error" :closable="false" show-icon class="mt-3" :title="previewError" />
      </section>

      <!-- Summary -->
      <section v-if="preview" class="mb-6">
        <h2 class="mb-2 text-sm font-semibold text-slate-700">Summary</h2>
        <div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          <div class="rounded border border-slate-200 bg-white px-3 py-2 text-center">
            <p class="text-lg font-semibold">{{ preview.summary.total }}</p>
            <p class="text-xs text-slate-500">Total rows</p>
          </div>
          <div class="rounded border border-green-200 bg-green-50 px-3 py-2 text-center">
            <p class="text-lg font-semibold text-green-800">{{ preview.summary.ok }}</p>
            <p class="text-xs text-green-700">OK</p>
          </div>
          <div class="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-center">
            <p class="text-lg font-semibold text-amber-800">{{ preview.summary.warnings }}</p>
            <p class="text-xs text-amber-700">Warnings</p>
          </div>
          <div class="rounded border border-red-200 bg-red-50 px-3 py-2 text-center">
            <p class="text-lg font-semibold text-red-800">{{ preview.summary.errors }}</p>
            <p class="text-xs text-red-700">Errors</p>
          </div>
          <div class="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-center">
            <p class="text-lg font-semibold">{{ preview.summary.duplicates }}</p>
            <p class="text-xs text-slate-500">Possible duplicates</p>
          </div>
          <div class="rounded border border-blue-200 bg-blue-50 px-3 py-2 text-center">
            <p class="text-lg font-semibold text-blue-800">{{ preview.summary.ready_to_import }}</p>
            <p class="text-xs text-blue-700">Ready to import</p>
          </div>
        </div>
        <el-alert
          v-for="(w, i) in preview.header_warnings"
          :key="`hw-${i}`"
          type="warning"
          :closable="false"
          show-icon
          class="mt-2"
          :title="w"
        />
      </section>

      <!-- Preview table -->
      <section v-if="preview" class="mb-6">
        <h2 class="mb-2 text-sm font-semibold text-slate-700">Preview</h2>
        <el-table :data="preview.rows" stripe border size="small" max-height="480">
          <el-table-column prop="row_number" label="Row" width="56" />
          <el-table-column prop="company_name" label="Company" min-width="140" show-overflow-tooltip />
          <el-table-column prop="contact_name" label="Contact" width="110" show-overflow-tooltip />
          <el-table-column prop="website" label="Website" min-width="120" show-overflow-tooltip />
          <el-table-column prop="company_type" label="Company Type" min-width="120" show-overflow-tooltip />
          <el-table-column prop="source" label="Source" width="100" show-overflow-tooltip />
          <el-table-column label="Likely Segments" min-width="160">
            <template #default="{ row }">
              <el-tag
                v-for="seg in row.likely_segments"
                :key="seg"
                size="small"
                class="mr-1 mb-1"
                :type="segmentTagType(seg)"
              >
                {{ segmentLabel(seg) }}
              </el-tag>
              <span v-if="!row.likely_segments.length" class="text-xs text-slate-400">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="priority_hint" label="Priority" width="80" />
          <el-table-column label="Missing Fields" min-width="120">
            <template #default="{ row }">
              <span v-if="row.missing_fields.length" class="text-xs text-amber-700">
                {{ row.missing_fields.join(', ') }}
              </span>
              <span v-else class="text-xs text-slate-400">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="duplicate_status" label="Duplicate" width="120">
            <template #default="{ row }">
              <el-tag size="small" :type="duplicateTagType(row.duplicate_status)">
                {{ row.duplicate_status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="recommended_next_action"
            label="Recommended Next Action"
            min-width="180"
            show-overflow-tooltip
          />
          <el-table-column prop="status" label="Status" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="statusTagType(row.status)">{{ row.status.toUpperCase() }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <!-- Confirm -->
      <section v-if="preview" class="mb-4">
        <el-button
          type="success"
          :loading="applyLoading"
          :disabled="!canImport"
          @click="confirmImport"
        >
          Confirm Import
        </el-button>
        <p v-if="preview.summary.errors > 0" class="mt-2 text-sm text-red-600">
          Fix ERROR rows before importing (missing company_name or invalid data).
        </p>
        <p v-else-if="preview.summary.warnings > 0" class="mt-2 text-sm text-amber-700">
          {{ preview.summary.warnings }} row(s) have warnings — you may still import after review.
        </p>
      </section>

      <!-- Apply result -->
      <section v-if="applyResult" class="mt-4 rounded border border-green-200 bg-green-50 p-4">
        <h2 class="mb-2 text-sm font-semibold text-green-900">Import complete</h2>
        <ul class="text-sm text-green-800">
          <li>Created companies: {{ applyResult.created_companies }}</li>
          <li>Skipped duplicates: {{ applyResult.skipped_duplicates }}</li>
          <li>Created contacts: {{ applyResult.created_contacts }}</li>
          <li>Linked leads: {{ applyResult.linked_leads }}</li>
        </ul>
        <ul v-if="applyResult.warnings.length" class="mt-2 text-xs text-amber-800">
          <li v-for="(w, i) in applyResult.warnings" :key="i">{{ w }}</li>
        </ul>
        <el-button type="primary" class="mt-3" @click="goToQueue">Go to Manual Outreach Queue</el-button>
      </section>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile } from 'element-plus'
import {
  applyLeadIntake,
  downloadCsvBlob,
  fetchLeadIntakeTemplate,
  LEAD_INTAKE_PRIVACY_NOTICE,
  LEAD_INTAKE_SAFETY_NOTICE,
  previewLeadIntake,
  type LeadIntakeApplyResponse,
  type LeadIntakePreviewResponse,
} from '@/api/leadImport'
import { formatApiError } from '@/api/errors'
import { segmentLabel, segmentTagType } from '@/constants/leadSegments'

const router = useRouter()

const csvText = ref('')
const inputTab = ref('paste')
const uploadFileName = ref('')
const preview = ref<LeadIntakePreviewResponse | null>(null)
const applyResult = ref<LeadIntakeApplyResponse | null>(null)
const previewLoading = ref(false)
const applyLoading = ref(false)
const templateLoading = ref(false)
const previewError = ref('')

const privacyBullets = `${LEAD_INTAKE_PRIVACY_NOTICE} This tool does not send messages. This tool does not contact LinkedIn or Outlook.`

const canImport = computed(() => {
  if (!preview.value) return false
  return preview.value.summary.errors === 0 && preview.value.summary.ready_to_import > 0
})

function statusTagType(status: string) {
  if (status === 'error') return 'danger'
  if (status === 'warn') return 'warning'
  return 'success'
}

function duplicateTagType(status: string) {
  if (status === 'existing') return 'danger'
  if (status === 'possible_duplicate') return 'warning'
  return 'info'
}

async function downloadTemplate() {
  templateLoading.value = true
  try {
    const content = await fetchLeadIntakeTemplate()
    downloadCsvBlob('lead_import_template.csv', content)
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e, 'Failed to download template'))
  } finally {
    templateLoading.value = false
  }
}

function onFileSelected(file: UploadFile) {
  const raw = file.raw
  if (!raw) return
  const reader = new FileReader()
  reader.onload = () => {
    csvText.value = String(reader.result || '')
    uploadFileName.value = file.name
    preview.value = null
    applyResult.value = null
    previewError.value = ''
  }
  reader.readAsText(raw, 'UTF-8')
}

async function runPreview() {
  previewLoading.value = true
  previewError.value = ''
  preview.value = null
  applyResult.value = null
  try {
    preview.value = await previewLeadIntake(csvText.value)
  } catch (e: unknown) {
    previewError.value = formatApiError(e, 'Preview failed')
  } finally {
    previewLoading.value = false
  }
}

async function confirmImport() {
  if (!preview.value || !canImport.value) return
  const hasWarn = preview.value.summary.warnings > 0
  try {
    if (hasWarn) {
      await ElMessageBox.confirm(
        `${preview.value.summary.warnings} row(s) have warnings. Import anyway?`,
        'Confirm import',
        { type: 'warning' },
      )
    } else {
      await ElMessageBox.confirm(
        `Import ${preview.value.summary.ready_to_import} lead row(s) into CRM?`,
        'Confirm import',
        { type: 'info' },
      )
    }
  } catch {
    return
  }

  applyLoading.value = true
  try {
    applyResult.value = await applyLeadIntake(csvText.value)
    ElMessage.success('Import complete — review leads in Manual Outreach Queue')
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e, 'Import failed'))
  } finally {
    applyLoading.value = false
  }
}

function goToQueue() {
  router.push({ name: 'lead-intelligence' })
}

function clearAll() {
  csvText.value = ''
  uploadFileName.value = ''
  preview.value = null
  applyResult.value = null
  previewError.value = ''
}
</script>
