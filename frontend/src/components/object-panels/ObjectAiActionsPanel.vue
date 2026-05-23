<template>
  <el-card shadow="never">
    <template #header>
      <span class="font-medium text-slate-800">AI 快捷动作</span>
    </template>
    <p class="mb-3 text-xs text-slate-500">
      输出写入 AI 产出表。未配置 API Key 时后端通常返回占位文案，仍可保存。网络或校验错误时会提示失败。
    </p>
    <div class="flex flex-wrap gap-2">
      <el-button
        v-for="a in visibleActions"
        :key="a.key"
        size="small"
        :loading="loading === a.key"
        @click="run(a)"
      >
        {{ a.label }}
      </el-button>
    </div>
    <p v-if="lastKind && lastKind.startsWith('li') && lastText" class="mt-2 text-xs text-slate-500">
      字符数（参考）：{{ lastText.length }} / 300
    </p>
    <div
      v-if="lastText"
      class="mt-4 max-h-64 overflow-auto rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-800 whitespace-pre-wrap"
    >
      {{ lastText }}
    </div>
    <p v-if="lastError" class="mt-2 text-xs text-rose-600">{{ lastError }}</p>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { http } from '@/api/http'
import type { ObjectType } from '@/constants/objectType'
import { ElMessage } from 'element-plus'
import axios from 'axios'

type PanelVariant =
  | 'default'
  | 'lead'
  | 'company'
  | 'contact'
  | 'manufacturing_partner'
  | 'product'
  | 'rfq'
  | 'sample'
  | 'order'

type AiAction = { key: string; label: string; path: string }

const props = defineProps<{
  objectType: ObjectType
  objectId: string
  aiContext?: Record<string, unknown>
  variant?: PanelVariant
}>()

const loading = ref<string | null>(null)
const lastText = ref('')
const lastKind = ref<string | null>(null)
const lastError = ref<string | null>(null)

const BASE: AiAction[] = [
  { key: 'follow', label: '跟进话术', path: '/ai/follow-up' },
  { key: 'email', label: '邮件草稿', path: '/ai/email' },
  { key: 'li', label: 'LinkedIn 备注', path: '/ai/linkedin-note' },
]

const BY_VARIANT: Record<PanelVariant, AiAction[]> = {
  default: BASE,
  lead: [
    ...BASE,
    { key: 'profile', label: '客户画像', path: '/ai/customer-profile' },
    { key: 'product', label: '产品推荐', path: '/ai/product-recommendation' },
  ],
  company: [
    { key: 'profile', label: '客户画像', path: '/ai/customer-profile' },
    { key: 'strategy', label: '触达策略', path: '/ai/company-outreach-strategy' },
    { key: 'intro', label: '初次邮件', path: '/ai/email' },
    { key: 'follow', label: '跟进邮件', path: '/ai/follow-up' },
    { key: 'categories', label: '品类建议', path: '/ai/recommend-product-categories' },
  ],
  contact: [
    { key: 'li', label: 'LinkedIn 备注', path: '/ai/linkedin-note' },
    { key: 'follow', label: '跟进话术', path: '/ai/follow-up' },
    { key: 'email', label: '邮件草稿', path: '/ai/email' },
    { key: 'role', label: '角色分析', path: '/ai/contact-role-analysis' },
    { key: 'meeting', label: '会议邀约', path: '/ai/meeting-request-email' },
  ],
  manufacturing_partner: [
    { key: 'psum', label: '英文摘要', path: '/ai/partner-english-summary' },
    { key: 'risk', label: '风险摘要', path: '/ai/supplier-risk-summary' },
    { key: 'fit', label: '产品匹配', path: '/ai/partner-product-fit' },
    { key: 'checklist', label: '缺失信息清单', path: '/ai/partner-missing-info-checklist' },
  ],
  product: [
    { key: 'desc', label: '英文描述', path: '/ai/product-english-description' },
    { key: 'short', label: '短销售段落', path: '/ai/product-short-sales-paragraph' },
    { key: 'customers', label: '客户类型建议', path: '/ai/recommend-customer-types' },
    { key: 'partners', label: '合作制造商建议', path: '/ai/match-partners-for-product' },
    { key: 'epar', label: '邮件段落', path: '/ai/email-paragraph' },
    { key: 'lipur', label: 'LinkedIn 产品话术', path: '/ai/linkedin-product-message' },
  ],
  rfq: [
    { key: 'rfqsum', label: 'RFQ 需求摘要', path: '/ai/rfq-requirement-summary' },
    { key: 'partrec', label: '推荐制造伙伴', path: '/ai/partner-recommendation' },
    { key: 'qcmp', label: '伙伴报价对比', path: '/ai/compare-partner-quotations' },
    { key: 'cqem', label: '客户报价邮件', path: '/ai/customer-quotation-email' },
    { key: 'pqrem', label: '伙伴询价邮件', path: '/ai/partner-quote-request-email' },
    { key: 'rfqfup', label: '跟进邮件', path: '/ai/rfq-follow-up-email' },
    { key: 'rfqmiss', label: '缺失信息清单', path: '/ai/rfq-missing-information-checklist' },
    { key: 'rfqrisk', label: '内部风险摘要', path: '/ai/rfq-internal-risk-summary' },
  ],
  sample: [
    { key: 'sfu', label: '样品跟进邮件', path: '/ai/sample-follow-up-email' },
    { key: 'sfr', label: '反馈索要', path: '/ai/sample-feedback-request' },
    { key: 'srisk', label: '内部风险摘要', path: '/ai/sample-internal-risk-summary' },
    { key: 'scu', label: '客户状态更新', path: '/ai/sample-customer-update' },
    { key: 'sns', label: '下一步建议', path: '/ai/sample-next-step-recommendation' },
  ],
  order: [
    { key: 'ocu', label: '客户更新邮件', path: '/ai/order-update-email' },
    { key: 'ode', label: '延误说明邮件', path: '/ai/order-delay-explanation-email' },
    { key: 'oir', label: '内部风险摘要', path: '/ai/order-internal-risk-summary' },
    { key: 'oss', label: '海运状态更新', path: '/ai/order-shipping-status-update' },
    { key: 'opf', label: '伙伴跟进话术', path: '/ai/order-partner-followup' },
    { key: 'ons', label: '下一步建议', path: '/ai/order-next-step-recommendation' },
  ],
}

const visibleActions = computed(() => BY_VARIANT[props.variant ?? 'default'] ?? BASE)

async function run(action: AiAction) {
  const ctx = { ...(props.aiContext ?? {}), object_type: props.objectType, object_id: props.objectId }
  const body = {
    context: ctx,
    input_object_type: props.objectType,
    input_object_id: props.objectId,
  }
  loading.value = action.key
  lastError.value = null
  try {
    const { data } = await http.post<{ output_text?: string | null }>(action.path, body)
    lastText.value = data.output_text || ''
    lastKind.value = action.key
    ElMessage.success('已生成')
  } catch (e: unknown) {
    let msg = '调用失败'
    if (axios.isAxiosError(e)) {
      const d = e.response?.data as { detail?: unknown } | undefined
      if (typeof d?.detail === 'string') msg = d.detail
      else if (Array.isArray(d?.detail)) msg = JSON.stringify(d?.detail)
      else if (e.message) msg = e.message
    }
    lastError.value = msg
    ElMessage.error(msg)
  } finally {
    loading.value = null
  }
}
</script>
