<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-semibold text-slate-900">Partner 接入管理</h1>
        <p class="mt-1 text-sm text-slate-600">
          用统一流程把优质外贸品牌接入 PartnerOS 运营闭环。
        </p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="所有制造伙伴平级管理。本页不会通知供应商或客户，不会验证 staging，不会创建 proof records，也不会进入 D9。"
    />
    <el-alert v-if="error" type="error" :closable="false" show-icon :title="error" />

    <el-skeleton v-if="loading && !data" animated :rows="8" />

    <template v-else-if="data">
      <section class="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <div v-for="metric in metrics" :key="metric.label" class="rounded border border-slate-200 bg-white p-3">
          <div class="text-xs uppercase text-slate-500">{{ metric.label }}</div>
          <div class="mt-1 text-2xl font-semibold text-slate-900">{{ metric.value }}</div>
        </div>
      </section>

      <OperationalTracePanel
        title="Daily Queue / Partner Onboarding 回流"
        description="显示 partner onboarding 缺口是否进入今日队列、谁接手、是否等待 business/security/partner 外部输入，以及下一次跟进。"
        category="partner onboarding"
      />

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="font-semibold text-slate-900">多品牌接入阶段</h2>
            <p class="mt-1 text-sm text-slate-600">
              每个 partner 都按发现、产品映射、报价准备、Portal 准备、演示准备和真实订单使用逐步推进。
            </p>
          </div>
          <el-tag type="info" effect="plain">{{ data.status }}</el-tag>
        </div>
        <div class="grid gap-2 md:grid-cols-4 xl:grid-cols-7">
          <div v-for="stage in data.stage_order" :key="stage" class="rounded border border-slate-200 p-3">
            <div class="text-xs uppercase text-slate-500">{{ stageLabel(stage) }}</div>
            <div class="mt-1 text-sm text-slate-700">{{ stageCount(stage) }} 个 partner</div>
          </div>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="font-semibold text-slate-900">接入记录</h2>
            <p class="mt-1 text-sm text-slate-600">
              HOSUN 和 JOOBOO 是参考样板；未来品牌按同一套 checklist 接入。
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <el-button size="small" @click="go('/demo-walkthrough')">演示流程</el-button>
            <el-button size="small" @click="go('/market-intelligence')">市场响应</el-button>
            <el-button size="small" @click="go('/orders')">订单</el-button>
          </div>
        </div>

        <el-table :data="data.items" border class="w-full" empty-text="暂无 partner 接入记录">
          <el-table-column label="Partner" min-width="240">
            <template #default="{ row }">
              <div class="font-medium text-slate-900">{{ row.partner_name }}</div>
              <div class="text-xs text-slate-500">{{ row.partner_type || '未分类' }}</div>
              <div class="mt-1 flex flex-wrap gap-1">
                <el-tag v-if="row.is_reference_partner" size="small" type="success" effect="plain">参考样板</el-tag>
                <el-tag size="small" type="info" effect="plain">{{ row.partner_code || '无代码' }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="阶段" min-width="145">
            <template #default="{ row }">
              <el-tag :type="stageType(row.onboarding_stage)" effect="plain">{{ stageLabel(row.onboarding_stage) }}</el-tag>
              <div class="mt-2 text-xs text-slate-500">{{ row.readiness_summary }}</div>
            </template>
          </el-table-column>
          <el-table-column label="就绪度" width="140">
            <template #default="{ row }">
              <el-progress :percentage="row.readiness_score" :stroke-width="8" />
            </template>
          </el-table-column>
          <el-table-column label="产品方向" min-width="240">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tag v-for="focus in row.product_focus" :key="focus" size="small" effect="plain">{{ focus }}</el-tag>
              </div>
              <div class="mt-2 text-xs text-slate-500">{{ row.target_markets.join(', ') }}</div>
            </template>
          </el-table-column>
          <el-table-column label="缺失项" min-width="260">
            <template #default="{ row }">
              <div v-if="row.missing_items.length" class="flex flex-wrap gap-1">
                <el-tag v-for="item in row.missing_items.slice(0, 4)" :key="item" type="warning" size="small" effect="plain">
                  {{ itemLabel(item) }}
                </el-tag>
              </div>
              <span v-else class="text-sm text-emerald-700">已可进入 active partner 运营</span>
            </template>
          </el-table-column>
          <el-table-column label="下一步动作" min-width="320">
            <template #default="{ row }">
              <p class="text-sm text-slate-700">{{ row.next_action }}</p>
            </template>
          </el-table-column>
          <el-table-column label="入口" width="160" fixed="right">
            <template #default="{ row }">
              <div class="flex flex-col gap-1">
                <el-button size="small" link type="primary" @click="go(row.links.partner_detail)">Partner</el-button>
                <el-button size="small" link type="primary" @click="go(row.links.product_catalog)">产品目录</el-button>
                <el-button size="small" link type="primary" @click="go(row.links.market_response)">市场响应</el-button>
                <el-button
                  size="small"
                  link
                  type="primary"
                  :disabled="!canCreateMarketReviews(row)"
                  :loading="creatingReviews === row.partner_id"
                  @click="createMarketReviews(row)"
                >
                  生成市场审查项
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="mb-3 font-semibold text-slate-900">接入 checklist</h2>
          <div class="grid gap-2 md:grid-cols-3">
            <div v-for="key in data.checklist_keys" :key="key" class="rounded border border-slate-200 p-3">
              <div class="text-sm font-medium text-slate-800">{{ itemLabel(key) }}</div>
              <div class="mt-1 text-xs text-slate-500">推进 partner readiness 前需要完成。</div>
            </div>
          </div>
        </div>

        <div v-if="data.future_partner_placeholder" class="rounded border border-dashed border-slate-300 bg-white p-4">
          <h2 class="font-semibold text-slate-900">未来 partner 占位</h2>
          <p class="mt-2 text-sm text-slate-600">{{ data.future_partner_placeholder.partner_name }}</p>
          <p class="mt-2 text-sm text-slate-700">{{ data.future_partner_placeholder.next_action }}</p>
          <div class="mt-3 flex flex-wrap gap-1">
            <el-tag v-for="item in data.future_partner_placeholder.missing_items.slice(0, 5)" :key="item" size="small" type="warning" effect="plain">
              {{ itemLabel(item) }}
            </el-tag>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  createPartnerOnboardingMarketResponseReviews,
  fetchPartnerOnboarding,
  type PartnerOnboardingRecord,
  type PartnerOnboardingResponse,
  type PartnerOnboardingStage,
} from '@/api/partnerOnboarding'
import OperationalTracePanel from '@/components/dashboard/OperationalTracePanel.vue'

const router = useRouter()
const data = ref<PartnerOnboardingResponse | null>(null)
const loading = ref(false)
const error = ref('')
const creatingReviews = ref<string | null>(null)

const metrics = computed(() => {
  const summary = data.value?.summary
  if (!summary) return []
  return [
    { label: 'Partner 总数', value: summary.total_partners },
    { label: '参考样板', value: summary.reference_partner_count },
    { label: '演示就绪', value: summary.demo_ready_count },
    { label: '报价就绪', value: summary.quote_ready_count },
    { label: 'Portal 就绪', value: summary.portal_ready_count },
    { label: '活跃伙伴', value: summary.active_partner_count },
  ]
})

function stageLabel(stage: string) {
  const labels: Record<string, string> = {
    discovery: '发现阶段',
    product_mapping: '产品映射',
    quote_ready: '报价就绪',
    portal_ready: 'Portal 就绪',
    demo_ready: '演示就绪',
    active_partner: '活跃伙伴',
    paused: '暂停',
  }
  return labels[stage] || stage.replaceAll('_', ' ')
}

function itemLabel(item: string) {
  const labels: Record<string, string> = {
    brand_profile_completed: '品牌资料完成',
    product_categories_mapped: '产品分类已映射',
    pricing_basis_available: '报价基础可用',
    quote_flow_ready: '报价流程就绪',
    order_flow_ready: '订单流程就绪',
    production_shipment_flow_mapped: '生产/物流已映射',
    portal_visibility_reviewed: 'Portal 可见字段已审查',
    market_response_focus_defined: '市场响应方向已定义',
    demo_narrative_prepared: '演示叙事已准备',
  }
  return labels[item] || item.replaceAll('_', ' ')
}

function stageCount(stage: string) {
  return data.value?.items.filter((row) => row.onboarding_stage === stage).length ?? 0
}

function stageType(stage: PartnerOnboardingStage) {
  if (stage === 'active_partner' || stage === 'demo_ready') return 'success'
  if (stage === 'portal_ready' || stage === 'quote_ready') return 'primary'
  if (stage === 'paused') return 'danger'
  return 'warning'
}

function go(path: string) {
  router.push(path)
}

function canCreateMarketReviews(row: PartnerOnboardingRecord) {
  return row.partner_id !== '00000000-0000-0000-0000-000000000000'
}

async function createMarketReviews(row: PartnerOnboardingRecord) {
  if (!canCreateMarketReviews(row)) {
    ElMessage.warning('请先创建真实 partner 记录，再生成 Market Response 审查项。')
    return
  }
  creatingReviews.value = row.partner_id
  error.value = ''
  try {
    const result = await createPartnerOnboardingMarketResponseReviews(row.partner_id)
    const createdCount = result.created?.length || 0
    const existingCount = result.existing?.length || 0
    ElMessage.success(`已同步审查项：新增 ${createdCount} 条，已有 ${existingCount} 条。`)
    await load()
    router.push(result.market_response_link || row.links.market_response)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Market Response 审查项生成失败'
  } finally {
    creatingReviews.value = null
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchPartnerOnboarding()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Partner 接入数据暂不可用'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
