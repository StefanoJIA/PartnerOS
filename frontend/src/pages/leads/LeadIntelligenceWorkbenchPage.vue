<template>
  <div class="space-y-4">
    <el-card v-loading="reviewLoading" shadow="never">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 class="text-lg font-semibold text-slate-800">Lead Completeness</h2>
            <p class="mt-1 text-xs text-slate-500">
              Profile gaps before outreach — contact, website, enrichment, and next action (D5.4)
            </p>
          </div>
        </div>
      </template>

      <div class="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
        <div class="rounded border border-slate-200 bg-slate-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-slate-800">{{ completenessSummary.total }}</p>
          <p class="text-xs text-slate-500">Total Leads</p>
        </div>
        <div class="rounded border border-green-200 bg-green-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-green-800">{{ completenessSummary.complete }}</p>
          <p class="text-xs text-green-700">Complete</p>
        </div>
        <div class="rounded border border-blue-200 bg-blue-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-blue-800">{{ completenessSummary.readyForOutreach }}</p>
          <p class="text-xs text-blue-700">Ready for Outreach</p>
        </div>
        <div class="rounded border border-violet-200 bg-violet-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-violet-800">{{ completenessSummary.needsContactResearch }}</p>
          <p class="text-xs text-violet-700">Needs Contact Research</p>
        </div>
        <div class="rounded border border-red-200 bg-red-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-red-800">{{ completenessSummary.incomplete }}</p>
          <p class="text-xs text-red-700">Incomplete</p>
        </div>
        <div class="rounded border border-amber-200 bg-amber-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-amber-800">{{ completenessSummary.missingWebsite }}</p>
          <p class="text-xs text-amber-700">Missing Website</p>
        </div>
        <div class="rounded border border-orange-200 bg-orange-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-orange-800">{{ completenessSummary.missingContactMethod }}</p>
          <p class="text-xs text-orange-700">Missing Contact Method</p>
        </div>
      </div>

      <p class="mb-1 text-xs font-medium text-slate-600">Completeness filters</p>
      <el-radio-group v-model="completenessFilter" size="small" class="mb-3 flex flex-wrap gap-1">
        <el-radio-button v-for="opt in COMPLETENESS_FILTER_OPTIONS" :key="opt.key" :value="opt.key">
          {{ opt.label }}
        </el-radio-button>
      </el-radio-group>

      <el-table
        :data="filteredCompletenessRows"
        size="small"
        stripe
        highlight-current-row
        :empty-text="completenessEmptyText"
        @row-click="onCompletenessRowClick"
      >
        <el-table-column prop="companyName" label="Company" min-width="130" show-overflow-tooltip />
        <el-table-column label="Score" width="64" sortable :sort-method="sortCompletenessByScore">
          <template #default="{ row }">
            <span class="font-semibold">{{ row.score }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Status" width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="completenessStatusTagType(row.status)" effect="plain">
              {{ row.statusLabel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Missing Fields" min-width="140">
          <template #default="{ row }">
            <span v-if="row.missingFields.length" class="text-xs text-amber-700">
              {{ row.missingFields.map((f) => MISSING_FIELD_LABELS[f] || f).join(', ') }}
            </span>
            <span v-else class="text-xs text-slate-400">—</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="recommendedResearchAction"
          label="Recommended Research Action"
          min-width="180"
          show-overflow-tooltip
        />
        <el-table-column label="Segment" min-width="120">
          <template #default="{ row }">
            <el-tag v-if="row.segments[0]" size="small" :type="segmentTagType(row.segments[0])" effect="plain">
              {{ segmentLabel(row.segments[0]) }}
            </el-tag>
            <span v-else class="text-xs text-slate-400">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="nextAction" label="Next Action" min-width="120" show-overflow-tooltip />
        <el-table-column prop="lastTouch" label="Last Touchpoint" min-width="100" show-overflow-tooltip />
        <el-table-column label="" width="130" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click.stop="openContactResearch(row)">
              Research / Edit
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <ContactResearchDrawer
      v-model:visible="contactResearchVisible"
      :row="contactResearchRow"
      :initial="contactResearchInitial"
      @saved="onContactResearchSaved"
    />

    <el-card v-loading="reviewLoading" shadow="never">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 class="text-lg font-semibold text-slate-800">Manual Outreach Queue</h2>
            <p class="mt-1 text-xs text-slate-500">
              Daily follow-up rhythm - score, segment, outreach status, and next actions (D5.2.8)
            </p>
          </div>
          <el-button size="small" @click="loadReviewBoard">Refresh</el-button>
        </div>
      </template>

      <el-alert type="info" :closable="false" show-icon class="mb-3" :title="OUTREACH_SAFETY_NOTICE" />

      <el-alert
        v-if="reviewBoardError"
        type="warning"
        :closable="false"
        show-icon
        class="mb-3"
        title="Could not load outreach queue"
        :description="reviewBoardError"
      />

      <div class="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
        <div class="rounded border border-slate-200 bg-slate-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-slate-800">{{ dailySummary.total }}</p>
          <p class="text-xs text-slate-500">Total Leads</p>
        </div>
        <div class="rounded border border-blue-100 bg-blue-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-blue-800">{{ dailySummary.needs_first_outreach }}</p>
          <p class="text-xs text-blue-600">Needs First Outreach</p>
        </div>
        <div class="rounded border border-amber-100 bg-amber-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-amber-800">{{ dailySummary.waiting_for_reply }}</p>
          <p class="text-xs text-amber-600">Waiting for Reply</p>
        </div>
        <div class="rounded border border-orange-100 bg-orange-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-orange-800">{{ dailySummary.follow_up_soon }}</p>
          <p class="text-xs text-orange-600">Follow Up Soon</p>
        </div>
        <div class="rounded border border-violet-100 bg-violet-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-violet-800">{{ dailySummary.needs_contact_research }}</p>
          <p class="text-xs text-violet-600">Needs Contact Research</p>
        </div>
        <div class="rounded border border-rose-100 bg-rose-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-rose-800">{{ dailySummary.high_priority }}</p>
          <p class="text-xs text-rose-600">High Priority</p>
        </div>
        <div class="rounded border border-slate-200 bg-white px-2 py-2 text-center">
          <p class="text-lg font-semibold text-slate-700">{{ dailySummary.needs_enrichment }}</p>
          <p class="text-xs text-slate-500">Needs Enrichment</p>
        </div>
      </div>

      <div class="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-5 lg:grid-cols-5">
        <div class="rounded border border-red-200 bg-red-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-red-800">{{ followUpSummary.overdue }}</p>
          <p class="text-xs text-red-600">Overdue</p>
        </div>
        <div class="rounded border border-amber-200 bg-amber-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-amber-800">{{ followUpSummary.due_today }}</p>
          <p class="text-xs text-amber-700">Due Today</p>
        </div>
        <div class="rounded border border-orange-200 bg-orange-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-orange-800">{{ followUpSummary.due_soon }}</p>
          <p class="text-xs text-orange-700">Due Soon</p>
        </div>
        <div class="rounded border border-slate-200 bg-slate-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-slate-800">{{ followUpSummary.no_follow_up_date }}</p>
          <p class="text-xs text-slate-500">No Follow-up Date</p>
        </div>
        <div class="rounded border border-blue-200 bg-blue-50 px-2 py-2 text-center">
          <p class="text-lg font-semibold text-blue-800">{{ followUpSummary.waiting_reply }}</p>
          <p class="text-xs text-blue-600">Waiting Reply</p>
        </div>
      </div>

      <p class="mb-1 text-xs font-medium text-slate-600">Due queue filters (D5.7)</p>
      <el-radio-group v-model="dueQueueFilter" size="small" class="mb-2 flex flex-wrap gap-1">
        <el-radio-button v-for="opt in DUE_QUEUE_FILTER_OPTIONS" :key="opt.key" :value="opt.key">
          {{ opt.label }}
        </el-radio-button>
      </el-radio-group>

      <p class="mb-1 text-xs font-medium text-slate-600">Operation filters</p>
      <el-radio-group v-model="queueFilter" size="small" class="mb-2 flex flex-wrap gap-1">
        <el-radio-button v-for="opt in OPERATION_FILTER_OPTIONS" :key="opt.key" :value="opt.key">
          {{ opt.label }}
        </el-radio-button>
      </el-radio-group>

      <p class="mb-1 text-xs font-medium text-slate-600">Segment &amp; legacy filters</p>
      <el-radio-group v-model="queueFilter" size="small" class="mb-3 flex flex-wrap gap-1">
        <el-radio-button v-for="opt in SEGMENT_AND_LEGACY_FILTER_OPTIONS" :key="opt.key" :value="opt.key">
          {{ opt.label }}
        </el-radio-button>
      </el-radio-group>

      <el-table
        :data="filteredReviewRows"
        size="small"
        stripe
        highlight-current-row
        :empty-text="queueEmptyText"
        @row-click="onReviewRowClick"
      >
        <el-table-column prop="companyName" label="Company" min-width="130" show-overflow-tooltip />
        <el-table-column label="Status" width="118">
          <template #default="{ row }">
            <el-tag v-if="row.statusBadge" size="small" effect="plain" type="warning">
              {{ statusBadgeLabel(row.statusBadge) }}
            </el-tag>
            <span v-else class="text-xs text-slate-400">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="contactName" label="Contact" width="110" show-overflow-tooltip />
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
        <el-table-column label="Follow-up" width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-xs">{{ row.nextFollowUpDate || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Due" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="dueStatusTagType(row.dueStatus)" effect="plain">
              {{ DUE_STATUS_LABELS[row.dueStatus as DueStatus] || row.dueStatus }}
            </el-tag>
            <span v-if="row.daysUntilDue != null" class="ml-1 text-xs text-slate-500">
              {{ formatDaysUntilDue(row.daysUntilDue) }}
            </span>
          </template>
        </el-table-column>
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

            <el-card shadow="never">
              <template #header>最近触达记录</template>
              <ul v-if="recentInteractions.length" class="space-y-2 text-sm text-slate-600">
                <li v-for="ix in recentInteractions" :key="ix.id" class="border-b border-slate-100 pb-2 last:border-0">
                  <span class="font-medium">{{ ix.interaction_type }}</span>
                  <span v-if="ix.channel"> · {{ ix.channel }}</span>
                  <span v-if="ix.interaction_date" class="text-xs text-slate-400"> · {{ formatDate(ix.interaction_date) }}</span>
                  <p class="text-xs">{{ ix.summary || ix.subject || '—' }}</p>
                </li>
              </ul>
              <p v-else class="text-sm text-slate-500">No touchpoints yet.</p>
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

            <ProductFitCard :lead-id="selectedLeadId" />

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
                <el-button size="small" @click="applyContactResearchTouchPreset">Contact research preset</el-button>
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

            <FollowUpScheduler
              ref="followUpSchedulerRef"
              :lead-id="selectedLeadId"
              :initial-date="wf.lead.next_action_due_date ?? null"
              :initial-next-action="wf.lead.next_action ?? null"
              :suggested-date="followUpSuggestedDate"
              @saved="onFollowUpSaved"
            />

            <OutreachHistoryTimeline ref="timelineRef" :lead-id="selectedLeadId" />
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
import { fetchLeadIntelligenceWorkflow, fetchFollowUpQueue, postLeadIntelligenceTouchpoint } from '@/api/aDomain'
import { listEnrichmentRuns } from '@/api/companyEnrichment'
import { http } from '@/api/http'
import {
  segmentLabel,
  segmentTagType,
  segmentTooltip,
  priorityHint,
  SEGMENT_FILTER_OPTIONS,
} from '@/constants/leadSegments'
import {
  classifyFollowUpCategories,
  computeDailySummary,
  OPERATION_FILTER_OPTIONS,
  primaryStatusBadge,
  STATUS_BADGE_LABELS,
  type FollowUpCategory,
} from '@/constants/followUpRhythm'
import {
  draftStatusLabel,
  filterQueueRows,
  LEGACY_QUEUE_FILTER_OPTIONS,
  OUTREACH_SAFETY_NOTICE,
  recommendChannel,
  type DraftStatus,
  type QueueFilterKey,
} from '@/constants/outreachQueue'
import {
  COMPLETENESS_FILTER_OPTIONS,
  MISSING_FIELD_LABELS,
  applyContactResearchPreset,
  computeCompletenessSummary,
  computeLeadCompleteness,
  completenessStatusTagType,
  filterCompletenessRows,
  type CompletenessFilterKey,
  type CompletenessRow,
} from '@/constants/leadCompleteness'
import {
  CHANNEL_PRESETS,
  NEXT_ACTION_SUGGESTIONS,
  TOUCHPOINT_TYPE_PRESETS,
} from '@/constants/touchpointPresets'
import OutreachDraftPanel from '@/components/outreach/OutreachDraftPanel.vue'
import ContactResearchDrawer from '@/components/leads/ContactResearchDrawer.vue'
import OutreachHistoryTimeline from '@/components/leads/OutreachHistoryTimeline.vue'
import FollowUpScheduler from '@/components/leads/FollowUpScheduler.vue'
import ProductFitCard from '@/components/leads/ProductFitCard.vue'
import {
  DUE_QUEUE_FILTER_OPTIONS,
  DUE_STATUS_LABELS,
  type DueQueueFilterKey,
  type DueStatus,
  dueStatusTagType,
  filterByDueQueue,
  formatDaysUntilDue,
  quickFollowUpDates,
} from '@/constants/followUpScheduling'
import { formatApiError } from '@/api/errors'

type ContactResearchInitial = {
  website?: string | null
  companyType?: string | null
  companyNotes?: string | null
  contactName?: string | null
  contactTitle?: string | null
  contactEmail?: string | null
  contactPhone?: string | null
  linkedinUrl?: string | null
  nextAction?: string | null
}

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
  lastTouchDate: string | null
  touchCount: number
  enrichmentStatus: string
  companyWebsite: string | null
  followUpCategories: FollowUpCategory[]
  statusBadge: FollowUpCategory | null
  priorityHint: string
  recommendedChannel: string
  recommendedChannelKey: string
  recommendedProductFocus: string
  contactTitle: string | null
  contactLinkedinUrl: string | null
  contactPhone: string | null
  suggestedNextActions: string[]
  companyNotes: string | null
  businessDescription: string | null
  industry: string | null
  nextFollowUpDate: string | null
  dueStatus: DueStatus | string
  daysUntilDue: number | null
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
const reviewBoardError = ref('')
const queueFilter = ref<QueueFilterKey>('today_focus')
const dueQueueFilter = ref<DueQueueFilterKey>('all')
const completenessFilter = ref<CompletenessFilterKey>('all')
const draftStatusByLead = ref<Record<string, DraftStatus>>({})
const recentInteractions = ref<InteractionBrief[]>([])
const contactResearchVisible = ref(false)
const contactResearchRow = ref<CompletenessRow | null>(null)
const timelineRef = ref<{ reload: () => Promise<void> } | null>(null)
const followUpSchedulerRef = ref<{ reload?: () => void } | null>(null)
const followUpSuggestedDate = ref<string | null>(null)
const followUpSummary = ref({
  total: 0,
  overdue: 0,
  due_today: 0,
  due_soon: 0,
  no_follow_up_date: 0,
  waiting_reply: 0,
})
const waitingByLead = ref<Record<string, boolean>>({})

async function refreshTimeline() {
  await timelineRef.value?.reload()
}

const SEGMENT_AND_LEGACY_FILTER_OPTIONS = [...SEGMENT_FILTER_OPTIONS, ...LEGACY_QUEUE_FILTER_OPTIONS]

const dailySummary = computed(() => computeDailySummary(reviewRows.value))

function statusBadgeLabel(cat: FollowUpCategory): string {
  return STATUS_BADGE_LABELS[cat]
}

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

const filteredReviewRows = computed(() => {
  const rhythmFiltered = filterQueueRows(reviewRows.value, queueFilter.value)
  return filterByDueQueue(rhythmFiltered, dueQueueFilter.value, waitingByLead.value)
})

const completenessRows = computed<CompletenessRow[]>(() =>
  reviewRows.value.map((row) => {
    const comp = computeLeadCompleteness({
      companyName: row.companyName,
      companyType: row.companyType !== '—' ? row.companyType : null,
      industry: row.industry,
      notes: row.companyNotes,
      businessDescription: row.businessDescription,
      website: row.companyWebsite,
      contactName: row.contactName !== '—' ? row.contactName : null,
      contactTitle: row.contactTitle,
      contactEmail: row.contactEmail,
      contactLinkedinUrl: row.contactLinkedinUrl,
      companyLinkedinUrl: row.linkedinUrl,
      contactPhone: row.contactPhone,
      segments: row.segments,
      intelligenceScore: row.score,
      suggestedNextActions: row.suggestedNextActions,
      nextAction: row.nextAction,
      enrichmentStatus: row.enrichmentStatus,
      touchCount: row.touchCount,
    })
    return {
      leadId: row.leadId,
      companyName: row.companyName,
      score: comp.score,
      status: comp.status,
      statusLabel: comp.statusLabel,
      missingFields: comp.missingFields,
      recommendedResearchAction: comp.recommendedResearchAction,
      segments: row.segments,
      nextAction: row.nextAction,
      lastTouch: row.lastTouch,
    }
  }),
)

const filteredCompletenessRows = computed(() =>
  filterCompletenessRows(completenessRows.value, completenessFilter.value),
)

const completenessSummary = computed(() => computeCompletenessSummary(completenessRows.value))

const completenessEmptyText = computed(() => {
  if (reviewLoading.value) return 'Loading completeness...'
  if (!completenessRows.value.length) return 'No leads — refresh or import leads.'
  if (!filteredCompletenessRows.value.length) return 'No leads match this completeness filter.'
  return 'No leads.'
})

const queueEmptyText = computed(() => {
  if (reviewLoading.value) return 'Loading leads...'
  if (!reviewRows.value.length) return 'No leads in queue - refresh or import leads.'
  if (!filteredReviewRows.value.length) return 'No leads match this filter.'
  return 'No leads in queue - refresh or import leads.'
})

function sortByScore(a: ReviewRow, b: ReviewRow) {
  return a.score - b.score
}

function sortCompletenessByScore(a: CompletenessRow, b: CompletenessRow) {
  return a.score - b.score
}

function onCompletenessRowClick(row: CompletenessRow) {
  selectedLeadId.value = row.leadId
}

const contactResearchInitial = computed((): ContactResearchInitial | null => {
  if (!contactResearchRow.value) return null
  const review = reviewRows.value.find((r) => r.leadId === contactResearchRow.value?.leadId)
  if (!review) return null
  return {
    website: review.companyWebsite,
    companyType: review.companyType,
    companyNotes: review.companyNotes,
    contactName: review.contactName,
    contactTitle: review.contactTitle,
    contactEmail: review.contactEmail,
    contactPhone: review.contactPhone,
    linkedinUrl: review.contactLinkedinUrl ?? review.linkedinUrl,
    nextAction: review.nextAction,
  }
})

function openContactResearch(row: CompletenessRow) {
  contactResearchRow.value = row
  contactResearchVisible.value = true
}

async function onContactResearchSaved() {
  await loadReviewBoard()
  const id = contactResearchRow.value?.leadId || selectedLeadId.value
  if (id) {
    selectedLeadId.value = id
    await loadWorkflow(id)
  }
  await refreshTimeline()
}

function applyContactResearchTouchPreset() {
  applyContactResearchPreset(touch.value)
  ElMessage.info('Contact research preset applied — save when ready.')
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

watch(
  () => route.query.filter,
  (f) => {
    if (typeof f !== 'string' || !f) return
    const dueKeys: DueQueueFilterKey[] = [
      'overdue',
      'due_today',
      'due_soon',
      'no_follow_up_date',
      'scheduled',
      'waiting_reply',
    ]
    if (dueKeys.includes(f as DueQueueFilterKey)) {
      dueQueueFilter.value = f as DueQueueFilterKey
      return
    }
    const compKeys: CompletenessFilterKey[] = [
      'complete',
      'ready_for_outreach',
      'needs_contact_research',
      'incomplete',
      'missing_website',
      'missing_email_linkedin',
      'missing_next_action',
      'missing_enrichment',
    ]
    if (compKeys.includes(f as CompletenessFilterKey)) {
      completenessFilter.value = f as CompletenessFilterKey
    }
  },
  { immediate: true },
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
    ElMessage.error(formatApiError(e, '加载工作流失败'))
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadReviewBoard() {
  reviewLoading.value = true
  reviewBoardError.value = ''
  try {
    const { data } = await http.get<{ items: { id: string; lead_name: string; next_action?: string | null; priority?: string | null }[] }>(
      '/leads',
      { params: { limit: 100 } },
    )
    const leads = data.items || []
    leadOptions.value = leads.map((l) => ({ id: l.id, lead_name: l.lead_name }))

    const enrichCache = new Map<string, string>()

    let fuMap = new Map<string, import('@/api/aDomain').FollowUpQueueRow>()
    try {
      const fq = await fetchFollowUpQueue()
      followUpSummary.value = fq.summary
      fuMap = new Map(fq.rows.map((r) => [r.lead_id, r]))
      waitingByLead.value = Object.fromEntries(fq.rows.map((r) => [r.lead_id, r.waiting_reply]))
    } catch {
      /* follow-up queue optional if backend older */
    }

    const rows = await Promise.all(
      leads.map(async (lead): Promise<ReviewRow | null> => {
        try {
          const w = await fetchLeadIntelligenceWorkflow(lead.id)
          let lastTouch = '—'
          let lastTouchDate: string | null = null
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
              lastTouchDate = t.interaction_date || null
            }
          } catch {
            /* optional */
          }

          const contactName = w.primary_contact
            ? `${w.primary_contact.first_name} ${w.primary_contact.last_name}`.trim()
            : '—'
          const contactEmail = w.primary_contact?.email ?? null
          const contactTitle = w.primary_contact?.title ?? null
          const contactLinkedinUrl = w.primary_contact?.linkedin_url ?? null
          const contactPhone = w.primary_contact?.phone ?? null
          const linkedinUrl = contactLinkedinUrl ?? w.company.linkedin_url ?? null
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

          const rhythmBase = {
            score: w.intelligence_score,
            segments: w.market_fit_segments || [],
            nextAction: (lead.next_action || w.lead.next_action || '').trim() || 'No next action set.',
            touchCount,
            lastTouch,
            lastTouchDate,
            contactEmail,
            linkedinUrl,
            enrichmentStatus: enrichCache.get(cid) || '—',
            companyWebsite: w.company.website ?? null,
          }
          const followUpCategories = classifyFollowUpCategories(rhythmBase)

          const followUp = fuMap.get(lead.id)

          return {
            leadId: lead.id,
            leadName: lead.lead_name,
            companyName: w.company.company_name,
            companyType: w.company.company_type || '—',
            contactName,
            contactEmail,
            linkedinUrl,
            contactTitle,
            contactLinkedinUrl,
            contactPhone,
            suggestedNextActions: w.suggested_next_actions || [],
            companyNotes: (w.company as { notes?: string | null }).notes ?? null,
            businessDescription: w.company.business_description ?? null,
            industry: (w.company as { industry?: string | null }).industry ?? null,
            score: rhythmBase.score,
            segments: rhythmBase.segments,
            priority: lead.priority ?? w.lead.priority ?? '—',
            nextAction: rhythmBase.nextAction,
            lastTouch,
            lastTouchDate,
            touchCount,
            enrichmentStatus: rhythmBase.enrichmentStatus,
            companyWebsite: rhythmBase.companyWebsite,
            followUpCategories,
            statusBadge: primaryStatusBadge(followUpCategories),
            priorityHint: priorityHint(w.intelligence_score, lead.priority ?? w.lead.priority),
            recommendedChannel: rec.label,
            recommendedChannelKey: rec.channel || 'email_intro',
            recommendedProductFocus: rec.productFocus,
            nextFollowUpDate: followUp?.next_follow_up_date ?? w.lead.next_action_due_date ?? null,
            dueStatus: (followUp?.due_status ?? 'no_follow_up_date') as DueStatus,
            daysUntilDue: followUp?.days_until_due ?? null,
          }
        } catch {
          return null
        }
      }),
    )
    reviewRows.value = rows.filter((r): r is ReviewRow => r !== null)
  } catch (e: unknown) {
    reviewBoardError.value = formatApiError(e, 'Failed to load Lead Review board.')
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
  followUpSuggestedDate.value = quickFollowUpDates().in5Days
  ElMessage.info('Mark as Sent recorded. Set follow-up date to 5 days from now in Follow-up Scheduler if needed.')
  await loadWorkflow(selectedLeadId.value)
  await loadReviewBoard()
  await refreshTimeline()
}

async function onFollowUpSaved() {
  followUpSuggestedDate.value = null
  if (selectedLeadId.value) {
    await loadWorkflow(selectedLeadId.value)
  }
  await loadReviewBoard()
  await refreshTimeline()
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
    await refreshTimeline()
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
