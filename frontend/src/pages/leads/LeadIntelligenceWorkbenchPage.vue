<template>
  <div class="space-y-4">
    <el-card v-loading="reviewLoading" shadow="never">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 class="text-lg font-semibold text-slate-800">Manual Outreach Queue</h2>
            <p class="mt-1 text-xs text-slate-500">
              Daily lead development — score, segment, draft, and manual send tracking (D5.2.5)
            </p>
          </div>
          <el-button size="small" @click="loadReviewBoard">Refresh</el-button>
        </div>
      </template>

      <el-alert type="info" :closable="false" show-icon class="mb-3" :title="OUTREACH_SAFETY_NOTICE" />

      <el-radio-group v-model="queueFilter" size="small" class="mb-3 flex flex-wrap gap-1">
        <el-radio-button v-for="opt in QUEUE_FILTER_OPTIONS" :key="opt.key" :value="opt.key">
          {{ opt.label }}
        </el-radio-button>
      </el-radio-group>

      <el-table
        :data="filteredReviewRows"
        size="small"
        stripe
        highlight-current-row
        empty-text="No leads in queue — refresh or import leads."
        @row-click="onReviewRowClick"
      >
        <el-table-column prop="companyName" label="Company" min-width="140" show-overflow-tooltip />
        <el-table-column prop="contactName" label="Contact" width="120" show-overflow-tooltip />
        <el-table-column label="Score" width="64" sortable :sort-method="sortByScore">
          <template #default="{ row }">
            <span class="font-semibold">{{ row.score }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Segment" min-width="150">
          <template #default="{ row }">
            <div v-if="row.segments.length" class="flex flex-wrap gap-1">
              <el-tag
                v-for="seg in row.segments.slice(0, 2)"
                :key="seg"
                size="small"
                :type="segmentTagType(seg)"
                effect="plain"
              >
                {{ segmentLabel(seg) }}
              </el-tag>
            </div>
            <span v-else class="text-xs text-slate-400">No segment</span>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="Priority" width="72" show-overflow-tooltip />
        <el-table-column prop="lastTouch" label="Last touch" min-width="100" show-overflow-tooltip />
        <el-table-column prop="nextAction" label="Next action" min-width="120" show-overflow-tooltip />
        <el-table-column prop="recommendedChannel" label="Channel" width="130" show-overflow-tooltip />
        <el-table-column label="Draft" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ draftStatusLabel(draftStatusByLead[row.leadId] || 'none') }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="enrichmentStatus" label="Enrichment" width="100" show-overflow-tooltip />
      </el-table>
    </el-card>

    <div v-loading="loading" class="space-y-4">
      <el-card shadow="never">
        <template #header>
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 class="text-lg font-semibold text-slate-800">A 域 · Lead Intelligence 工作台</h2>
              <p class="mt-1 text-xs text-slate-500">
                公司 → 联系人 → 情报标签 / 市场信号 → 可解释评分 → 互动记录 → 下一步动作
              </p>
            </div>
            <el-select
              v-model="selectedLeadId"
              filterable
              clearable
              placeholder="选择线索"
              class="min-w-[240px]"
              :loading="leadsLoading"
              @visible-change="onLeadsDropdown"
            >
              <el-option v-for="l in leadOptions" :key="l.id" :label="l.lead_name" :value="l.id" />
            </el-select>
          </div>
        </template>
        <p v-if="!selectedLeadId" class="text-sm text-slate-500">
          从上方 Review 表点击一行，或选择线索以加载详情。
        </p>
      </el-card>

      <template v-if="wf && selectedLeadId">
        <el-row :gutter="16">
          <el-col :xs="24" :lg="14">
            <el-card shadow="never" class="mb-4">
              <template #header>公司与联系人</template>
              <div class="space-y-2 text-sm">
                <div>
                  <span class="font-medium text-slate-700">{{ wf.company.company_name }}</span>
                  <el-tag v-if="wf.company.company_type" size="small" class="ml-2" effect="plain">
                    {{ wf.company.company_type }}
                  </el-tag>
                  <router-link
                    class="ml-2 text-xs text-blue-600"
                    :to="{ name: 'company-detail', params: { companyId: wf.company.id } }"
                  >
                    公司详情
                  </router-link>
                </div>
                <div v-if="wf.company.strategic_level" class="text-slate-600">
                  战略层级：{{ wf.company.strategic_level }}
                </div>
                <div class="text-slate-600">
                  <span class="font-medium">意向标签：</span>
                  {{ wf.company.product_interest_tags || '—' }}
                </div>
                <div class="text-slate-600">
                  <span class="font-medium">业务描述：</span>
                  {{ wf.company.business_description || '—' }}
                </div>
                <el-divider class="my-2" />
                <div v-if="wf.primary_contact">
                  <span class="font-medium">主联系人：</span>
                  {{ wf.primary_contact.first_name }} {{ wf.primary_contact.last_name }}
                  <span v-if="wf.primary_contact.title"> · {{ wf.primary_contact.title }}</span>
                  <router-link
                    class="ml-2 text-xs text-blue-600"
                    :to="{ name: 'contact-detail', params: { contactId: wf.primary_contact.id } }"
                  >
                    联系人
                  </router-link>
                </div>
                <el-alert v-else type="warning" :closable="false" show-icon title="未设置主联系人" class="mt-2" />
              </div>
            </el-card>

            <el-card shadow="never" class="mb-4">
              <template #header>线索与市场情报</template>
              <div class="space-y-2 text-sm text-slate-700">
                <div>
                  <span class="font-medium">{{ wf.lead.lead_name }}</span>
                  <router-link class="ml-2 text-xs text-blue-600" :to="{ name: 'lead-detail', params: { leadId: wf.lead.id } }">
                    线索详情
                  </router-link>
                </div>
                <div>阶段：{{ wf.lead.current_stage }} · 优先级：{{ wf.lead.priority || '—' }}</div>
                <div>商机意向：{{ wf.lead.product_interest || '—' }}</div>
                <div>
                  已关联市场情报条目：
                  <strong>{{ wf.market_intelligence_count }}</strong>
                </div>
              </div>
            </el-card>

            <el-card v-if="recentInteractions.length" shadow="never">
              <template #header>最近触达记录</template>
              <ul class="space-y-2 text-sm text-slate-600">
                <li v-for="ix in recentInteractions" :key="ix.id" class="border-b border-slate-100 pb-2 last:border-0">
                  <span class="font-medium">{{ ix.interaction_type }}</span>
                  <span v-if="ix.channel"> · {{ ix.channel }}</span>
                  <span v-if="ix.interaction_date" class="text-xs text-slate-400"> · {{ formatDate(ix.interaction_date) }}</span>
                  <p class="text-xs">{{ ix.summary || ix.subject || '—' }}</p>
                </li>
              </ul>
            </el-card>
          </el-col>

          <el-col :xs="24" :lg="10">
            <el-card shadow="never" class="mb-4">
              <template #header>情报评分（可解释）</template>
              <div v-if="wf.market_fit_segments?.length" class="mb-3 flex flex-wrap gap-1">
                <el-tag
                  v-for="seg in wf.market_fit_segments"
                  :key="seg"
                  size="small"
                  :type="segmentTagType(seg)"
                  effect="plain"
                  :title="segmentTooltip(seg)"
                >
                  {{ segmentLabel(seg) }}
                </el-tag>
              </div>
              <p v-else class="mb-3 text-xs text-slate-500">No segment assigned yet.</p>
              <div class="mb-3 text-center">
                <span class="text-4xl font-bold text-slate-800">{{ wf.intelligence_score }}</span>
                <span class="text-slate-500">/100</span>
              </div>
              <p class="mb-2 text-center text-xs text-slate-500">
                {{ priorityHint(wf.intelligence_score, wf.lead.priority) }}
              </p>
              <el-table :data="scoreRows" size="small" stripe>
                <el-table-column prop="k" label="维度" />
                <el-table-column prop="v" label="得分" width="72" />
              </el-table>
              <ul v-if="wf.suggested_next_actions?.length" class="mt-3 list-disc space-y-1 pl-5 text-xs text-slate-600">
                <li v-for="(s, i) in wf.suggested_next_actions" :key="i">{{ s }}</li>
              </ul>
              <p v-else class="mt-3 text-xs text-slate-500">No suggestions available yet.</p>
            </el-card>

            <el-card shadow="never" class="mb-4">
              <template #header>记录触达并更新 Next Action</template>
              <el-alert
                v-if="!wf.lead.next_action?.trim()"
                type="info"
                :closable="false"
                show-icon
                class="mb-3"
                title="No next action set."
                description="Set a clear follow-up below so this lead appears in your daily review."
              />
              <p v-else class="mb-3 text-sm text-slate-600">
                <span class="font-medium">当前 Next Action：</span>
                {{ wf.lead.next_action }}
                <span v-if="wf.lead.next_action_due_date" class="text-xs text-slate-400">
                  · due {{ wf.lead.next_action_due_date }}
                </span>
              </p>

              <div class="mb-3 flex flex-wrap gap-1">
                <el-button
                  v-for="s in NEXT_ACTION_SUGGESTIONS.slice(0, 4)"
                  :key="s"
                  size="small"
                  @click="touch.next_action = s"
                >
                  {{ s.length > 28 ? s.slice(0, 28) + '…' : s }}
                </el-button>
              </div>

              <el-form label-position="top" class="text-sm">
                <el-form-item label="互动类型">
                  <el-select v-model="touch.interaction_type" filterable allow-create class="w-full">
                    <el-option
                      v-for="p in TOUCHPOINT_TYPE_PRESETS"
                      :key="p.value"
                      :label="p.label"
                      :value="p.value"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="渠道">
                  <el-select v-model="touch.channel" filterable allow-create class="w-full">
                    <el-option v-for="p in CHANNEL_PRESETS" :key="p.value" :label="p.label" :value="p.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="主题">
                  <el-input v-model="touch.subject" />
                </el-form-item>
                <el-form-item label="摘要">
                  <el-input v-model="touch.summary" type="textarea" :rows="2" />
                </el-form-item>
                <el-form-item label="线索下一步（写入 Lead.next_action）">
                  <el-input v-model="touch.next_action" placeholder="e.g. Send catalog — waiting for reply" />
                </el-form-item>
                <el-form-item label="下次跟进日">
                  <el-date-picker v-model="touchDue" type="date" value-format="YYYY-MM-DD" class="w-full" />
                </el-form-item>
              <el-button type="primary" :loading="saving" @click="submitTouchpoint">保存互动与下一步</el-button>
            </el-form>
            </el-card>

            <OutreachDraftPanel
              :company-id="wf.company.id"
              :lead-id="selectedLeadId"
              :initial-channel="selectedChannelRec.channel"
              :initial-product-focus="selectedChannelRec.productFocus"
              @use-next-action="(v) => (touch.next_action = v)"
              @draft-status="onDraftStatus"
              @marked-sent="onMarkedSent"
            />
          </el-col>
        </el-row>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { LeadIntelligenceWorkflow, TouchpointBody } from '@/api/aDomain'
import { fetchLeadIntelligenceWorkflow, postLeadIntelligenceTouchpoint } from '@/api/aDomain'
import { listEnrichmentRuns } from '@/api/companyEnrichment'
import { http } from '@/api/http'
import {
  segmentLabel,
  segmentTagType,
  segmentTooltip,
  priorityHint,
} from '@/constants/leadSegments'
import {
  draftStatusLabel,
  filterQueueRows,
  OUTREACH_SAFETY_NOTICE,
  QUEUE_FILTER_OPTIONS,
  recommendChannel,
  type DraftStatus,
  type QueueFilterKey,
} from '@/constants/outreachQueue'
import {
  CHANNEL_PRESETS,
  NEXT_ACTION_SUGGESTIONS,
  TOUCHPOINT_TYPE_PRESETS,
} from '@/constants/touchpointPresets'
import OutreachDraftPanel from '@/components/outreach/OutreachDraftPanel.vue'

type ReviewRow = {
  leadId: string
  leadName: string
  companyName: string
  companyType: string
  contactName: string
  contactEmail: string | null
  linkedinUrl: string | null
  score: number
  segments: string[]
  priority: string | null
  nextAction: string
  lastTouch: string
  touchCount: number
  enrichmentStatus: string
  priorityHint: string
  recommendedChannel: string
  recommendedChannelKey: string
  recommendedProductFocus: string
}

type InteractionBrief = {
  id: string
  interaction_type: string
  channel?: string | null
  subject?: string | null
  summary?: string | null
  interaction_date?: string | null
}

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const reviewLoading = ref(false)
const leadsLoading = ref(false)
const saving = ref(false)
const wf = ref<LeadIntelligenceWorkflow | null>(null)
const leadOptions = ref<{ id: string; lead_name: string }[]>([])
const selectedLeadId = ref<string | null>((route.query.leadId as string) || null)
const reviewRows = ref<ReviewRow[]>([])
const queueFilter = ref<QueueFilterKey>('all')
const draftStatusByLead = ref<Record<string, DraftStatus>>({})
const recentInteractions = ref<InteractionBrief[]>([])

const selectedChannelRec = computed(() => {
  const row = reviewRows.value.find((r) => r.leadId === selectedLeadId.value)
  if (row) {
    return {
      channel: row.recommendedChannelKey,
      productFocus: row.recommendedProductFocus,
    }
  }
  if (wf.value) {
    const rec = recommendChannel(
      wf.value.market_fit_segments || [],
      wf.value.primary_contact?.email,
      wf.value.company.linkedin_url,
    )
    return { channel: rec.channel || 'linkedin_connect', productFocus: rec.productFocus }
  }
  return { channel: 'linkedin_connect', productFocus: 'general' }
})

const touch = ref<TouchpointBody>({
  interaction_type: 'follow_up',
  channel: 'phone',
  subject: '',
  summary: '',
  next_action: '',
  interaction_next_action: '',
})
const touchDue = ref<string | null>(null)

const scoreRows = computed(() => {
  if (!wf.value) return []
  return Object.entries(wf.value.score_breakdown).map(([k, v]) => ({ k, v }))
})

const filteredReviewRows = computed(() => filterQueueRows(reviewRows.value, queueFilter.value))

function sortByScore(a: ReviewRow, b: ReviewRow) {
  return a.score - b.score
}

function formatDate(iso: string) {
  try {
    return iso.slice(0, 10)
  } catch {
    return iso
  }
}

function displayEnrichmentStatus(status: string, pending: number): string {
  const s = (status || '').toLowerCase()
  if (s === 'completed') return pending > 0 ? `Completed (${pending} pending)` : 'Completed'
  if (s === 'running') return 'Running'
  if (s === 'failed') return 'Failed'
  if (s === 'pending') return 'Pending'
  return status || '—'
}

watch(
  () => route.query.leadId,
  (q) => {
    if (typeof q === 'string' && q) selectedLeadId.value = q
  },
)

watch(selectedLeadId, (id) => {
  if (id) {
    router.replace({ query: { ...route.query, leadId: id } })
    void loadWorkflow(id)
  } else {
    wf.value = null
    recentInteractions.value = []
    router.replace({ query: { ...route.query, leadId: undefined } })
  }
})

function onReviewRowClick(row: ReviewRow) {
  selectedLeadId.value = row.leadId
}

async function loadLeadsOnce() {
  if (leadOptions.value.length) return
  leadsLoading.value = true
  try {
    const { data } = await http.get<{ items: { id: string; lead_name: string }[] }>('/leads', { params: { limit: 100 } })
    leadOptions.value = data.items
  } finally {
    leadsLoading.value = false
  }
}

function onLeadsDropdown(open: boolean) {
  if (open) void loadLeadsOnce()
}

async function loadRecentInteractions(leadId: string) {
  try {
    const { data } = await http.get<{ items: InteractionBrief[]; total: number }>(
      `/objects/lead/${leadId}/interactions`,
      { params: { limit: 5 } },
    )
    recentInteractions.value = data.items || []
  } catch {
    recentInteractions.value = []
  }
}

async function loadWorkflow(leadId: string) {
  loading.value = true
  try {
    wf.value = await fetchLeadIntelligenceWorkflow(leadId)
    touch.value = {
      interaction_type: 'follow_up',
      channel: 'phone',
      subject: `Follow-up · ${wf.value.lead.lead_name}`,
      summary: '',
      next_action: wf.value.lead.next_action || '',
      interaction_next_action: '',
    }
    touchDue.value = wf.value.lead.next_action_due_date || null
    await loadRecentInteractions(leadId)
  } catch (e: unknown) {
    wf.value = null
    ElMessage.error('加载工作流失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadReviewBoard() {
  reviewLoading.value = true
  try {
    const { data } = await http.get<{ items: { id: string; lead_name: string; next_action?: string | null; priority?: string | null }[] }>(
      '/leads',
      { params: { limit: 100 } },
    )
    const leads = data.items || []
    leadOptions.value = leads.map((l) => ({ id: l.id, lead_name: l.lead_name }))

    const enrichCache = new Map<string, string>()

    const rows = await Promise.all(
      leads.map(async (lead): Promise<ReviewRow | null> => {
        try {
          const w = await fetchLeadIntelligenceWorkflow(lead.id)
          let lastTouch = '—'
          let touchCount = 0
          try {
            const { data: ix } = await http.get<{ items: InteractionBrief[]; total: number }>(
              `/objects/lead/${lead.id}/interactions`,
              { params: { limit: 1 } },
            )
            touchCount = ix.total || 0
            if (ix.items?.[0]) {
              const t = ix.items[0]
              lastTouch = t.summary || t.subject || t.interaction_type || '—'
            }
          } catch {
            /* optional */
          }

          const contactName = w.primary_contact
            ? `${w.primary_contact.first_name} ${w.primary_contact.last_name}`.trim()
            : '—'
          const contactEmail = w.primary_contact?.email ?? null
          const linkedinUrl = w.company.linkedin_url ?? null
          const rec = recommendChannel(w.market_fit_segments || [], contactEmail, linkedinUrl)

          const cid = w.company.id
          if (!enrichCache.has(cid)) {
            try {
              const runs = await listEnrichmentRuns(cid, 1)
              if (runs.total > 0 && runs.items[0]) {
                const r = runs.items[0]
                enrichCache.set(cid, displayEnrichmentStatus(r.status, r.pending_suggestion_count))
              } else {
                enrichCache.set(cid, 'No runs')
              }
            } catch {
              enrichCache.set(cid, '—')
            }
          }

          return {
            leadId: lead.id,
            leadName: lead.lead_name,
            companyName: w.company.company_name,
            companyType: w.company.company_type || '—',
            contactName,
            contactEmail,
            linkedinUrl,
            score: w.intelligence_score,
            segments: w.market_fit_segments || [],
            priority: lead.priority ?? w.lead.priority ?? '—',
            nextAction: (lead.next_action || w.lead.next_action || '').trim() || 'No next action set.',
            lastTouch,
            touchCount,
            enrichmentStatus: enrichCache.get(cid) || '—',
            priorityHint: priorityHint(w.intelligence_score, lead.priority ?? w.lead.priority),
            recommendedChannel: rec.label,
            recommendedChannelKey: rec.channel || 'email_intro',
            recommendedProductFocus: rec.productFocus,
          }
        } catch {
          return null
        }
      }),
    )
    reviewRows.value = rows.filter((r): r is ReviewRow => r !== null)
  } catch (e: unknown) {
    ElMessage.error('加载 Lead Review 失败')
    console.error(e)
  } finally {
    reviewLoading.value = false
  }
}

function onDraftStatus(s: DraftStatus) {
  if (!selectedLeadId.value) return
  draftStatusByLead.value = { ...draftStatusByLead.value, [selectedLeadId.value]: s }
}

async function onMarkedSent() {
  if (!selectedLeadId.value) return
  draftStatusByLead.value[selectedLeadId.value] = 'sent'
  await loadWorkflow(selectedLeadId.value)
  await loadReviewBoard()
}

async function submitTouchpoint() {
  if (!selectedLeadId.value) return
  saving.value = true
  try {
    await postLeadIntelligenceTouchpoint(selectedLeadId.value, {
      ...touch.value,
      next_action_due_date: touchDue.value || undefined,
    })
    ElMessage.success('Touchpoint saved — next action updated.')
    await loadWorkflow(selectedLeadId.value)
    await loadReviewBoard()
  } catch (e: unknown) {
    ElMessage.error('保存失败')
    console.error(e)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void loadReviewBoard()
  if (selectedLeadId.value) void loadWorkflow(selectedLeadId.value)
})
</script>
