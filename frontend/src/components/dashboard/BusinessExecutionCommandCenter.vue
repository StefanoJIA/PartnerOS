<template>
  <section class="rounded border border-slate-200 bg-white p-4">
    <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="text-base font-semibold text-slate-900">经营执行主链</h3>
        <p class="mt-1 max-w-4xl text-sm text-slate-600">
          把客户生命周期、项目机会、报价经验、产品验证、Partner 能力和交付风险合并成管理层每天可执行的经营判断。
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <el-tag type="primary" effect="plain">客户 {{ data?.summary.lifecycle_accounts ?? 0 }}</el-tag>
        <el-tag type="success" effect="plain">机会 {{ data?.summary.active_opportunities ?? 0 }}</el-tag>
        <el-tag type="warning" effect="plain">报价经验 {{ data?.summary.quote_learning_items ?? 0 }}</el-tag>
        <el-tag type="danger" effect="plain">交付风险 {{ data?.summary.delivery_risks ?? 0 }}</el-tag>
        <el-tag type="info" effect="plain">Partner 投入 {{ data?.summary.partner_investment_items ?? 0 }}</el-tag>
      </div>
    </div>

    <el-alert
      class="mb-4"
      type="warning"
      :closable="false"
      show-icon
      title="只读经营判断层：不自动发送外部消息、不改报价或订单状态、不记录 raw token、不把本地信息写成真实 staging evidence。"
    />

    <div v-if="!data" class="rounded border border-slate-100 bg-slate-50 p-4 text-sm text-slate-500">
      正在加载经营执行主链。
    </div>

    <template v-else>
      <div class="grid gap-3 lg:grid-cols-3">
        <div
          v-for="item in data.executive_decisions"
          :key="item.decision_id"
          class="rounded border border-slate-100 bg-slate-50 p-3"
        >
          <div class="mb-2 flex items-start justify-between gap-2">
            <h4 class="font-semibold text-slate-900">{{ item.question }}</h4>
            <el-tag :type="priorityType(item.priority)" effect="plain">{{ item.priority }}</el-tag>
          </div>
          <p class="text-sm text-slate-700">{{ item.answer }}</p>
          <p class="mt-2 text-xs text-slate-500">Owner: {{ item.owner }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ item.next_action }}</p>
          <el-button class="mt-2" size="small" type="primary" plain @click="go(item.path)">进入处理</el-button>
        </div>
      </div>

      <div class="mt-4 grid gap-4 xl:grid-cols-2">
        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">客户生命周期</h4>
            <el-button size="small" link type="primary" @click="go('/lead-intelligence')">客户开发</el-button>
          </div>
          <el-table :data="data.lifecycle.slice(0, 6)" size="small" border empty-text="暂无客户生命周期数据">
            <el-table-column label="客户 / 阶段" min-width="180">
              <template #default="{ row }">
                <div class="font-medium text-slate-800">{{ row.customer_name }}</div>
                <div class="mt-1 flex flex-wrap gap-1">
                  <el-tag size="small" effect="plain">{{ row.lifecycle_stage }}</el-tag>
                  <el-tag size="small" :type="priorityType(row.priority)" effect="plain">{{ row.priority }}</el-tag>
                  <el-tag size="small" type="info" effect="plain">{{ lifecycleSourceLabel(row.source_type) }}</el-tag>
                </div>
                <div class="mt-1 text-xs text-slate-500">{{ row.partner_focus || 'future partner' }}</div>
              </template>
            </el-table-column>
            <el-table-column label="下一步 / 阻碍" min-width="260">
              <template #default="{ row }">
                <p class="text-xs text-slate-500">{{ row.current_signal }}</p>
                <p class="text-xs text-slate-700">{{ row.next_action }}</p>
                <p v-if="row.blocker" class="mt-1 text-xs text-rose-600">{{ row.blocker }}</p>
                <div class="mt-1 flex flex-wrap gap-1">
                  <el-tag v-for="impact in row.readiness_impact.slice(0, 3)" :key="impact" size="small" effect="plain">
                    {{ impact }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="入口" width="90">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="go(row.path)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">项目机会管线</h4>
            <el-button size="small" link type="primary" @click="go('/growth-operations')">增长运营</el-button>
          </div>
          <el-table :data="data.opportunities.slice(0, 6)" size="small" border empty-text="暂无机会数据">
            <el-table-column label="机会 / Partner" min-width="210">
              <template #default="{ row }">
                <div class="font-medium text-slate-800">{{ row.opportunity_name }}</div>
                <div class="mt-1 text-xs text-slate-500">{{ row.partner_focus || 'future partner' }}</div>
              </template>
            </el-table-column>
            <el-table-column label="概率 / 风险" min-width="220">
              <template #default="{ row }">
                <el-progress :percentage="row.probability" :stroke-width="8" />
                <p class="mt-1 text-xs text-slate-600">{{ row.risk }}</p>
              </template>
            </el-table-column>
            <el-table-column label="入口" width="90">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="go(row.path)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">报价经验沉淀</h4>
            <el-button size="small" link type="primary" @click="go('/quotes')">报价</el-button>
          </div>
          <el-table :data="data.quotations.slice(0, 5)" size="small" border empty-text="暂无报价数据">
            <el-table-column label="报价 / 状态" min-width="150">
              <template #default="{ row }">
                <div class="font-medium text-slate-800">{{ row.quote_number }}</div>
                <el-tag class="mt-1" size="small" effect="plain">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="经验缺口" min-width="260">
              <template #default="{ row }">
                <p class="text-xs text-slate-700">{{ row.outcome_signal }}</p>
                <p class="mt-1 text-xs text-amber-700">{{ row.learning_signal }}</p>
              </template>
            </el-table-column>
            <el-table-column label="入口" width="90">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="go(row.path)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">产品 / Market Intelligence</h4>
            <el-button size="small" link type="primary" @click="go('/market-response')">市场响应</el-button>
          </div>
          <div class="space-y-2">
            <div v-for="item in data.products.slice(0, 5)" :key="item.partner_focus + item.validation_signal" class="rounded bg-slate-50 p-2">
              <div class="flex flex-wrap items-center gap-1">
                <el-tag size="small" effect="plain">{{ item.partner_focus }}</el-tag>
                <el-tag v-for="dimension in item.dimensions.slice(0, 5)" :key="dimension" size="small" type="info" effect="plain">
                  {{ dimension }}
                </el-tag>
              </div>
              <p class="mt-1 text-xs text-slate-700">{{ item.validation_signal }}</p>
              <p class="mt-1 text-xs text-rose-600">{{ item.risk }}</p>
            </div>
          </div>
        </section>

        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">Partner Intelligence</h4>
            <el-button size="small" link type="primary" @click="go('/partner-onboarding')">Partner 接入</el-button>
          </div>
          <div class="grid gap-2 md:grid-cols-2">
            <div v-for="item in data.partners.slice(0, 6)" :key="item.partner_id" class="rounded bg-slate-50 p-2">
              <div class="font-medium text-slate-800">{{ item.partner_name }}</div>
              <p class="mt-1 text-xs text-slate-600">{{ item.readiness_level }} / {{ item.delivery_ability }}</p>
              <p class="mt-1 text-xs text-rose-600">{{ item.risk_assessment }}</p>
            </div>
          </div>
        </section>

        <section class="rounded border border-slate-100 p-3">
          <div class="mb-2 flex items-center justify-between">
            <h4 class="font-semibold text-slate-900">项目交付透明度</h4>
            <el-button size="small" link type="primary" @click="go('/orders')">订单</el-button>
          </div>
          <el-table :data="data.delivery.slice(0, 5)" size="small" border empty-text="暂无交付数据">
            <el-table-column label="订单 / 风险" min-width="150">
              <template #default="{ row }">
                <div class="font-medium text-slate-800">{{ row.order_number }}</div>
                <el-tag class="mt-1" size="small" :type="riskType(row.risk_level)" effect="plain">{{ row.risk_level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="交付信号" min-width="280">
              <template #default="{ row }">
                <p class="text-xs text-slate-700">{{ row.production_signal }}</p>
                <p class="mt-1 text-xs text-slate-600">{{ row.shipment_signal }}</p>
                <p class="mt-1 text-xs text-amber-700">{{ row.repeat_business_risk }}</p>
              </template>
            </el-table-column>
            <el-table-column label="入口" width="90">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="go(row.path)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { BusinessExecution } from '@/api/dashboard'

defineProps<{
  data: BusinessExecution | null
}>()

const router = useRouter()

function go(path: string) {
  router.push(path)
}

function priorityType(priority: string) {
  if (priority === 'P0') return 'danger'
  if (priority === 'P1') return 'warning'
  return 'info'
}

function riskType(risk: string) {
  if (risk === 'high') return 'danger'
  if (risk === 'medium') return 'warning'
  return 'info'
}

function lifecycleSourceLabel(sourceType: string) {
  if (sourceType === 'lead') return '线索'
  if (sourceType === 'opportunity') return '机会'
  if (sourceType === 'quote') return '报价'
  if (sourceType === 'order') return '订单'
  if (sourceType === 'feedback') return '反馈'
  return sourceType
}
</script>
