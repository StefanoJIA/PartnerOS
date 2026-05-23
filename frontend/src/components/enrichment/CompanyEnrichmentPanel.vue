<template>
  <el-card shadow="never" class="mb-4">
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <span class="font-medium text-slate-800">公开来源 Enrichment（D5.2）</span>
          <p class="mt-1 text-xs text-slate-500">证据驱动建议 · 需人工审阅后写入正式画像</p>
        </div>
        <el-button
          type="primary"
          size="small"
          :loading="starting"
          :disabled="!website"
          @click="onStartRun"
        >
          运行 enrichment
        </el-button>
      </div>
    </template>
    <p v-if="!website" class="text-sm text-amber-700">该公司无网站 URL，无法从官网抓取。</p>
    <template v-else>
      <div v-if="latest" class="mb-3 text-sm text-slate-700">
        <div>
          最近运行：<strong>{{ displayRunStatus(latest) }}</strong> · 页数 {{ latest.pages_fetched }}/{{ latest.max_pages }} ·
          待审核建议 <strong>{{ latest.pending_suggestion_count }}</strong>
        </div>
        <div v-if="latest.completed_at" class="text-xs text-slate-500">完成时间：{{ latest.completed_at }}</div>
        <div v-if="latest.error_message" class="mt-1 text-xs text-red-600">{{ latest.error_message }}</div>
        <el-button class="mt-2" size="small" @click="openReview(latest.id)">审阅建议与证据</el-button>
      </div>
      <p v-else class="text-sm text-slate-500">Run enrichment to collect public evidence.</p>
    </template>

    <el-drawer v-model="drawer" title="Enrichment 审阅" size="70%">
      <div v-if="detailLoading" class="p-4 text-sm text-slate-500">加载中…</div>
      <template v-else-if="detail">
        <div class="mb-4 text-sm">
          <span>Run：{{ displayRunStatus(detail.run) }}</span>
          <span class="ml-2">来源页 {{ detail.sources.length }} 条</span>
        </div>
        <h4 class="mb-2 text-sm font-medium text-slate-700">来源（证据页）</h4>
        <el-table v-if="detail.sources.length" :data="detail.sources" size="small" class="mb-6" max-height="220">
          <el-table-column prop="page_type" label="类型" width="90" />
          <el-table-column label="URL" min-width="200">
            <template #default="{ row }">
              <a :href="row.url" target="_blank" rel="noreferrer" class="text-blue-600 text-xs break-all">{{
                row.url
              }}</a>
            </template>
          </el-table-column>
          <el-table-column prop="fetch_status" label="抓取" width="100" />
          <el-table-column prop="page_title" label="标题" show-overflow-tooltip />
        </el-table>
        <p v-else class="mb-6 text-sm text-slate-500">No evidence collected yet.</p>

        <div class="mb-2 flex flex-wrap gap-2">
          <el-button size="small" :disabled="!selectedIds.length" @click="batch('accepted')">批量接受选中</el-button>
          <el-button size="small" :disabled="!selectedIds.length" @click="batch('rejected')">批量拒绝选中</el-button>
        </div>

        <h4 class="mb-2 text-sm font-medium text-slate-700">建议（与正式标签分层展示）</h4>
        <el-table
          v-if="detail.suggestions.length"
          :data="detail.suggestions"
          size="small"
          max-height="360"
          @selection-change="onSel"
        >
          <el-table-column type="selection" width="42" :selectable="selectableRow" />
          <el-table-column prop="suggestion_type" label="类型" width="130" />
          <el-table-column label="建议值" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              {{ preview(row.suggested_value) }}
            </template>
          </el-table-column>
          <el-table-column prop="review_status" label="审阅" width="90" />
          <el-table-column label="证据摘录" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.evidence_snippet || '—' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.review_status === 'pending'"
                link
                type="primary"
                size="small"
                @click="review(row.id, 'accepted')"
              >
                接受
              </el-button>
              <el-button
                v-if="row.review_status === 'pending'"
                link
                size="small"
                @click="review(row.id, 'rejected')"
              >
                拒绝
              </el-button>
              <el-button
                v-if="row.review_status === 'accepted'"
                link
                type="success"
                size="small"
                @click="apply(row.id)"
              >
                写入正式画像
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <p v-else class="text-sm text-slate-500">No suggestions available yet.</p>
      </template>
    </el-drawer>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  applyEnrichmentSuggestion,
  batchReviewEnrichment,
  createEnrichmentRun,
  getEnrichmentRunDetail,
  listEnrichmentRuns,
  reviewEnrichmentSuggestion,
  type EnrichmentRunDetail,
  type EnrichmentRunSummary,
  type EnrichmentSuggestion,
} from '@/api/companyEnrichment'

const props = defineProps<{ companyId: string; website?: string | null }>()
const emit = defineEmits<{ reloaded: [] }>()

const starting = ref(false)
const runs = ref<EnrichmentRunSummary[]>([])
const drawer = ref(false)
const detailLoading = ref(false)
const detail = ref<EnrichmentRunDetail | null>(null)
const selectedIds = ref<string[]>([])

const latest = computed(() => runs.value[0] || null)

watch(
  () => props.companyId,
  () => loadList(),
)

onMounted(() => loadList())

async function loadList() {
  try {
    const data = await listEnrichmentRuns(props.companyId, 10)
    runs.value = data.items
  } catch {
    runs.value = []
  }
}

function selectableRow(row: EnrichmentSuggestion) {
  return row.review_status === 'pending'
}

function onSel(rows: EnrichmentSuggestion[]) {
  selectedIds.value = rows.map((r) => r.id)
}

function preview(v: string | null | undefined) {
  if (!v) return '—'
  if (v.length > 120) return v.slice(0, 117) + '…'
  return v
}

/** Fallback when API status is empty during poll or legacy rows (display-only). */
function displayRunStatus(run: EnrichmentRunSummary | null | undefined): string {
  if (!run) return '—'
  if (run.status) {
    const s = run.status.toLowerCase()
    if (s === 'completed') return 'Completed'
    if (s === 'running') return 'Running'
    if (s === 'failed') return 'Failed'
    if (s === 'pending') return 'Pending'
    return run.status
  }
  if (run.completed_at || run.pages_fetched > 0) return 'Completed'
  if (run.error_message) return 'Failed'
  return 'Unknown'
}

async function onStartRun() {
  if (!props.website) return
  starting.value = true
  try {
    await createEnrichmentRun(props.companyId)
    ElMessage.success('已启动 enrichment（后台抓取），请稍后刷新查看状态')
    await loadList()
    let n = 0
    const iv = setInterval(async () => {
      await loadList()
      n++
      const st = runs.value[0]?.status
      if (n >= 24 || st === 'completed' || st === 'failed') clearInterval(iv)
    }, 2500)
  } catch (e: unknown) {
    ElMessage.error('启动失败')
    console.error(e)
  } finally {
    starting.value = false
  }
}

async function openReview(runId: string) {
  drawer.value = true
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = await getEnrichmentRunDetail(runId)
  } catch (e: unknown) {
    ElMessage.error('加载审阅数据失败')
    console.error(e)
  } finally {
    detailLoading.value = false
  }
}

async function reloadDetail() {
  if (!detail.value) return
  await openReview(detail.value.run.id)
}

async function review(id: string, status: 'accepted' | 'rejected') {
  await reviewEnrichmentSuggestion(id, { review_status: status })
  ElMessage.success('已更新审阅状态')
  await reloadDetail()
  await loadList()
  emit('reloaded')
}

async function batch(status: 'accepted' | 'rejected') {
  if (!detail.value || !selectedIds.value.length) return
  await batchReviewEnrichment(detail.value.run.id, selectedIds.value, status)
  ElMessage.success('批量操作完成')
  selectedIds.value = []
  await reloadDetail()
  await loadList()
  emit('reloaded')
}

async function apply(id: string) {
  try {
    await applyEnrichmentSuggestion(props.companyId, id)
    ElMessage.success('已写入正式画像（按类型合并至公司字段或标签）')
    await reloadDetail()
    emit('reloaded')
  } catch (e: unknown) {
    ElMessage.error('应用失败')
    console.error(e)
  }
}
</script>
