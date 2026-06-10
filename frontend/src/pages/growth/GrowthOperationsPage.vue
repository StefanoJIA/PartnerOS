<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-semibold text-slate-900">增长运营闭环</h1>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          {{ data?.positioning_zh || '连接客户开发、Campaign、外联、报价、订单、Portal、反馈和市场响应。' }}
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <el-tag type="info" effect="plain">{{ data?.status || 'READY_FOR_STAGING_HANDOFF' }}</el-tag>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="安全边界：本页只做增长运营规划和人工动作记录，不连接销售易或 Constant Contact，不自动发送邮件/短信/LinkedIn，不修改报价或订单状态。"
    />
    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <el-skeleton v-if="loading && !data" animated :rows="8" />

    <template v-else-if="data">
      <section class="grid gap-3 lg:grid-cols-3">
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="font-semibold text-slate-900">销售易能力适配</h2>
          <div class="mt-3 flex flex-wrap gap-2">
            <el-tag v-for="item in data.competitor_alignment.sales_yi_adapted" :key="item" effect="plain">
              {{ item }}
            </el-tag>
          </div>
        </div>
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="font-semibold text-slate-900">Constant Contact 能力适配</h2>
          <div class="mt-3 flex flex-wrap gap-2">
            <el-tag v-for="item in data.competitor_alignment.constant_contact_adapted" :key="item" effect="plain">
              {{ item }}
            </el-tag>
          </div>
        </div>
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="font-semibold text-slate-900">PartnerOS 差异</h2>
          <p class="mt-3 text-sm text-slate-600">{{ data.competitor_alignment.partneros_difference }}</p>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="font-semibold text-slate-900">Campaign Planning</h2>
            <p class="mt-1 text-sm text-slate-600">
              每个 campaign 都绑定 partner focus、product focus、target segment、goal、status 和 next action。
            </p>
          </div>
          <el-tag type="success" effect="plain">HOSUN / JOOBOO / Future Partner 平级</el-tag>
        </div>
        <el-table :data="data.campaigns" border empty-text="暂无增长 campaign">
          <el-table-column label="Campaign" min-width="230">
            <template #default="{ row }">
              <div class="font-medium text-slate-900">{{ row.name }}</div>
              <div class="text-xs text-slate-500">{{ row.partner_focus }} · {{ row.status }}</div>
            </template>
          </el-table-column>
          <el-table-column label="产品方向" min-width="260">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tag v-for="item in row.product_focus" :key="item" size="small" effect="plain">{{ item }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="target_segment" label="目标分群" min-width="190" />
          <el-table-column prop="goal" label="目标" min-width="280" />
          <el-table-column prop="next_action" label="下一步" min-width="320" />
          <el-table-column label="运营数据" width="210">
            <template #default="{ row }">
              <div class="text-xs text-slate-600">
                线索 {{ row.metrics.lead_count }} / 报价 {{ row.metrics.quote_count }} / 订单 {{ row.metrics.order_count }}
              </div>
              <div class="mt-1 text-xs text-slate-600">
                反馈 {{ row.metrics.feedback_ticket_count }} / 物流风险 {{ row.metrics.shipment_risk_count }} / 市场信号 {{ row.metrics.market_signal_count }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="入口" width="160" fixed="right">
            <template #default="{ row }">
              <div class="flex flex-col gap-1">
                <el-button size="small" link type="primary" @click="go(row.links.lead_intelligence)">线索</el-button>
                <el-button size="small" link type="primary" @click="go(row.links.market_response)">市场响应</el-button>
                <el-button size="small" link type="primary" @click="go(row.links.quotes)">报价</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="mb-3 font-semibold text-slate-900">轻量客户分群</h2>
          <el-table :data="data.segments" stripe max-height="420" empty-text="暂无分群">
            <el-table-column prop="segment_label" label="分群" min-width="190" />
            <el-table-column prop="company_count" label="公司" width="80" />
            <el-table-column prop="lead_count" label="线索" width="80" />
            <el-table-column prop="contact_count" label="联系人" width="90" />
            <el-table-column prop="recommended_use" label="用途" min-width="260" />
          </el-table>
        </div>

        <div class="rounded border border-slate-200 bg-white p-4">
          <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 class="font-semibold text-slate-900">手动外联序列</h2>
            <el-select v-model="selectedCampaignId" size="small" class="w-64">
              <el-option v-for="row in data.campaigns" :key="row.id" :label="row.name" :value="row.id" />
            </el-select>
          </div>

          <template v-if="selectedSequence">
            <div class="mb-3 rounded border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
              <div>目标公司：{{ selectedSequence.company_name }}</div>
              <div>线索：{{ selectedSequence.lead_name || '暂无匹配线索，先做 segment 复核' }}</div>
              <div>任务：{{ selectedSequence.follow_up_task.title }} · {{ selectedSequence.follow_up_task.due_date }}</div>
            </div>

            <div class="grid gap-3 lg:grid-cols-2">
              <div>
                <p class="mb-1 text-xs font-medium text-slate-600">中文草稿</p>
                <el-input readonly :model-value="selectedSequence.drafts.zh.subject" class="mb-2" />
                <el-input type="textarea" :rows="7" readonly :model-value="selectedSequence.drafts.zh.body" />
              </div>
              <div>
                <p class="mb-1 text-xs font-medium text-slate-600">English Draft</p>
                <el-input readonly :model-value="selectedSequence.drafts.en.subject" class="mb-2" />
                <el-input type="textarea" :rows="7" readonly :model-value="selectedSequence.drafts.en.body" />
              </div>
            </div>

            <div class="mt-3 flex flex-wrap items-center gap-2">
              <el-select v-model="manualEvent" size="small" class="w-44">
                <el-option
                  v-for="item in selectedSequence.manual_event_options"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
              <el-button
                type="primary"
                size="small"
                :loading="recording"
                :disabled="!selectedSequence.lead_id"
                @click="recordManualEvent"
              >
                记录人工动作
              </el-button>
              <span class="text-xs text-slate-500">只写入 Lead touchpoint，不发送消息。</span>
            </div>
          </template>
        </div>
      </section>

      <section class="grid gap-5 xl:grid-cols-2">
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="mb-3 font-semibold text-slate-900">Campaign → Quote → Order 归因</h2>
          <el-table :data="data.attribution" stripe>
            <el-table-column label="Campaign" min-width="220">
              <template #default="{ row }">{{ campaignName(row.campaign_id) }}</template>
            </el-table-column>
            <el-table-column prop="quote_count" label="报价" width="80" />
            <el-table-column prop="order_count" label="订单" width="80" />
            <el-table-column prop="quote_value" label="报价金额" width="120" />
            <el-table-column prop="order_value" label="订单金额" width="120" />
            <el-table-column prop="explanation_zh" label="说明" min-width="260" />
          </el-table>
        </div>

        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="mb-3 font-semibold text-slate-900">反馈 / 物流风险 / 市场信号回流</h2>
          <el-table :data="data.feedback_loop" stripe>
            <el-table-column label="Campaign" min-width="220">
              <template #default="{ row }">{{ campaignName(row.campaign_id) }}</template>
            </el-table-column>
            <el-table-column prop="feedback_ticket_count" label="反馈" width="80" />
            <el-table-column prop="shipment_risk_count" label="物流风险" width="100" />
            <el-table-column prop="market_signal_count" label="市场信号" width="100" />
            <el-table-column prop="recommendation_zh" label="回流动作" min-width="260" />
          </el-table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { postLeadIntelligenceTouchpoint } from '@/api/aDomain'
import { formatApiError } from '@/api/errors'
import {
  fetchGrowthOperationsConsole,
  type GrowthOperationsConsole,
  type GrowthOutreachSequence,
} from '@/api/growthOperations'

const router = useRouter()
const data = ref<GrowthOperationsConsole | null>(null)
const loading = ref(false)
const error = ref('')
const selectedCampaignId = ref('')
const manualEvent = ref('manual_sent')
const recording = ref(false)

const selectedSequence = computed<GrowthOutreachSequence | null>(() => {
  if (!data.value) return null
  return data.value.outreach_sequences.find((row) => row.campaign_id === selectedCampaignId.value) || null
})

watch(selectedSequence, (row) => {
  manualEvent.value = row?.manual_event_options[0]?.value || 'manual_sent'
})

function campaignName(id: string): string {
  return data.value?.campaigns.find((row) => row.id === id)?.name || id
}

function go(path: string) {
  router.push(path)
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchGrowthOperationsConsole()
    if (!selectedCampaignId.value) selectedCampaignId.value = data.value.campaigns[0]?.id || ''
  } catch (err) {
    error.value = formatApiError(err, '增长运营数据加载失败。')
  } finally {
    loading.value = false
  }
}

async function recordManualEvent() {
  const sequence = selectedSequence.value
  if (!sequence?.lead_id) {
    ElMessage.warning('当前 campaign 暂无可记录的线索，请先在客户开发中补充线索。')
    return
  }
  recording.value = true
  try {
    const eventLabel = sequence.manual_event_options.find((item) => item.value === manualEvent.value)?.label || manualEvent.value
    await postLeadIntelligenceTouchpoint(sequence.lead_id, {
      interaction_type: 'growth_campaign_touchpoint',
      channel: sequence.channel,
      subject: `${campaignName(sequence.campaign_id)} · ${eventLabel}`,
      summary: `D8.13 增长运营记录：${eventLabel}。Campaign=${sequence.campaign_id}。仅记录人工动作，系统未自动发送。`,
      direction: 'outbound',
      next_action: sequence.follow_up_task.next_action,
      interaction_next_action: sequence.follow_up_task.next_action,
    })
    ElMessage.success('已记录人工增长触达动作。')
  } catch (err) {
    ElMessage.error(formatApiError(err, '人工动作记录失败。'))
  } finally {
    recording.value = false
  }
}

onMounted(load)
</script>
