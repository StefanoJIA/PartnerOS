<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-semibold text-slate-900">Partner onboarding</h1>
        <p class="mt-1 text-sm text-slate-600">
          Internal workflow for bringing premium export brands into the PartnerOS operating loop.
        </p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="load">Refresh</el-button>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="All manufacturing partners are peer partners. This page does not notify suppliers or customers, validate staging, create proof records, or enter D9."
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

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="font-semibold text-slate-900">Multi-brand operating ladder</h2>
            <p class="mt-1 text-sm text-slate-600">
              Move each partner through discovery, product mapping, quote readiness, Portal readiness, demo readiness, and active order use.
            </p>
          </div>
          <el-tag type="info" effect="plain">{{ data.status }}</el-tag>
        </div>
        <div class="grid gap-2 md:grid-cols-4 xl:grid-cols-7">
          <div v-for="stage in data.stage_order" :key="stage" class="rounded border border-slate-200 p-3">
            <div class="text-xs uppercase text-slate-500">{{ stageLabel(stage) }}</div>
            <div class="mt-1 text-sm text-slate-700">{{ stageCount(stage) }} partner(s)</div>
          </div>
        </div>
      </section>

      <section class="rounded border border-slate-200 bg-white p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="font-semibold text-slate-900">Onboarding records</h2>
            <p class="mt-1 text-sm text-slate-600">
              HOSUN and JOOBOO are reference examples; future brands follow the same checklist.
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <el-button size="small" @click="go('/demo-walkthrough')">Demo walkthrough</el-button>
            <el-button size="small" @click="go('/market-intelligence')">Market Response</el-button>
            <el-button size="small" @click="go('/orders')">Orders</el-button>
          </div>
        </div>

        <el-table :data="data.items" border class="w-full" empty-text="No partner records">
          <el-table-column label="Partner" min-width="240">
            <template #default="{ row }">
              <div class="font-medium text-slate-900">{{ row.partner_name }}</div>
              <div class="text-xs text-slate-500">{{ row.partner_type || 'Unclassified' }}</div>
              <div class="mt-1 flex flex-wrap gap-1">
                <el-tag v-if="row.is_reference_partner" size="small" type="success" effect="plain">reference sample</el-tag>
                <el-tag size="small" type="info" effect="plain">{{ row.partner_code || 'no code' }}</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="Stage" min-width="145">
            <template #default="{ row }">
              <el-tag :type="stageType(row.onboarding_stage)" effect="plain">{{ stageLabel(row.onboarding_stage) }}</el-tag>
              <div class="mt-2 text-xs text-slate-500">{{ row.readiness_summary }}</div>
            </template>
          </el-table-column>
          <el-table-column label="Readiness" width="140">
            <template #default="{ row }">
              <el-progress :percentage="row.readiness_score" :stroke-width="8" />
            </template>
          </el-table-column>
          <el-table-column label="Product focus" min-width="240">
            <template #default="{ row }">
              <div class="flex flex-wrap gap-1">
                <el-tag v-for="focus in row.product_focus" :key="focus" size="small" effect="plain">{{ focus }}</el-tag>
              </div>
              <div class="mt-2 text-xs text-slate-500">{{ row.target_markets.join(', ') }}</div>
            </template>
          </el-table-column>
          <el-table-column label="Missing items" min-width="260">
            <template #default="{ row }">
              <div v-if="row.missing_items.length" class="flex flex-wrap gap-1">
                <el-tag v-for="item in row.missing_items.slice(0, 4)" :key="item" type="warning" size="small" effect="plain">
                  {{ itemLabel(item) }}
                </el-tag>
              </div>
              <span v-else class="text-sm text-emerald-700">Ready for active partner operations</span>
            </template>
          </el-table-column>
          <el-table-column label="Next action" min-width="320">
            <template #default="{ row }">
              <p class="text-sm text-slate-700">{{ row.next_action }}</p>
            </template>
          </el-table-column>
          <el-table-column label="Links" width="160" fixed="right">
            <template #default="{ row }">
              <div class="flex flex-col gap-1">
                <el-button size="small" link type="primary" @click="go(row.links.partner_detail)">Partner</el-button>
                <el-button size="small" link type="primary" @click="go(row.links.product_catalog)">Catalog</el-button>
                <el-button size="small" link type="primary" @click="go(row.links.market_response)">Market</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <div class="rounded border border-slate-200 bg-white p-4">
          <h2 class="mb-3 font-semibold text-slate-900">Checklist contract</h2>
          <div class="grid gap-2 md:grid-cols-3">
            <div v-for="key in data.checklist_keys" :key="key" class="rounded border border-slate-200 p-3">
              <div class="text-sm font-medium text-slate-800">{{ itemLabel(key) }}</div>
              <div class="mt-1 text-xs text-slate-500">Required before advancing partner readiness.</div>
            </div>
          </div>
        </div>

        <div v-if="data.future_partner_placeholder" class="rounded border border-dashed border-slate-300 bg-white p-4">
          <h2 class="font-semibold text-slate-900">Future partner placeholder</h2>
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchPartnerOnboarding, type PartnerOnboardingResponse, type PartnerOnboardingStage } from '@/api/partnerOnboarding'

const router = useRouter()
const data = ref<PartnerOnboardingResponse | null>(null)
const loading = ref(false)
const error = ref('')

const metrics = computed(() => {
  const summary = data.value?.summary
  if (!summary) return []
  return [
    { label: 'Partners', value: summary.total_partners },
    { label: 'Reference samples', value: summary.reference_partner_count },
    { label: 'Demo ready', value: summary.demo_ready_count },
    { label: 'Quote ready', value: summary.quote_ready_count },
    { label: 'Portal ready', value: summary.portal_ready_count },
    { label: 'Active partner', value: summary.active_partner_count },
  ]
})

function stageLabel(stage: string) {
  return stage.replaceAll('_', ' ')
}

function itemLabel(item: string) {
  return item.replaceAll('_', ' ')
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

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchPartnerOnboarding()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Partner onboarding is unavailable'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

