/** D5.13 — product opportunity board constants */

import {
  MISSING_QUOTE_INFO_LABELS,
  OPPORTUNITY_LEVEL_LABELS,
  PRODUCT_FOCUS_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  opportunityLevelTagType,
  quoteReadinessTagType,
} from '@/constants/productFit'

export {
  PRODUCT_FOCUS_LABELS,
  OPPORTUNITY_LEVEL_LABELS,
  QUOTE_READINESS_LABELS,
  SAMPLE_READINESS_LABELS,
  MISSING_QUOTE_INFO_LABELS,
  opportunityLevelTagType,
  quoteReadinessTagType,
}

export const PRODUCT_OPPORTUNITY_SAFETY =
  '产品机会洞察仅作运营建议。intelliOffice 不会自动创建报价，也不承诺价格、库存、认证或交期。'

export type ProductOpportunityFilterKey =
  | 'all'
  | 'high_opportunity'
  | 'promising'
  | 'quote_ready'
  | 'almost_quote_ready'
  | 'sample_ready'
  | 'needs_specs'
  | 'lifting_system_fit'
  | 'project_supply'
  | 'education'
  | 'medical'
  | 'oem_odm'
  | 'missing_quantity'
  | 'missing_timeline'
  | 'missing_contact'

export const PRODUCT_OPPORTUNITY_FILTER_OPTIONS: { key: ProductOpportunityFilterKey; label: string }[] =
  [
    { key: 'all', label: '全部' },
    { key: 'high_opportunity', label: '高机会' },
    { key: 'promising', label: '值得跟进' },
    { key: 'quote_ready', label: '可报价' },
    { key: 'almost_quote_ready', label: '接近可报价' },
    { key: 'sample_ready', label: '可推进样品' },
    { key: 'needs_specs', label: '需补规格' },
    { key: 'lifting_system_fit', label: '升降系统' },
    { key: 'project_supply', label: '项目供应' },
    { key: 'education', label: '教育家具' },
    { key: 'medical', label: '医疗场景' },
    { key: 'oem_odm', label: 'OEM / ODM' },
    { key: 'missing_quantity', label: '缺少数量' },
    { key: 'missing_timeline', label: '缺少时间线' },
    { key: 'missing_contact', label: '缺少联系人' },
  ]

export const DASHBOARD_OPPORTUNITY_CARDS: {
  key: ProductOpportunityFilterKey
  label: string
  summaryKey: keyof ProductOpportunitySummaryKeys
  tone?: 'primary' | 'success' | 'warning' | 'info' | 'danger'
}[] = [
  { key: 'high_opportunity', label: '高机会', summaryKey: 'high_opportunity', tone: 'success' },
  { key: 'quote_ready', label: '可报价', summaryKey: 'quote_ready', tone: 'primary' },
  { key: 'almost_quote_ready', label: '接近可报价', summaryKey: 'almost_quote_ready', tone: 'warning' },
  { key: 'sample_ready', label: '可推进样品', summaryKey: 'sample_ready', tone: 'info' },
  { key: 'needs_specs', label: '需补规格', summaryKey: 'needs_specs', tone: 'warning' },
  { key: 'lifting_system_fit', label: '升降系统匹配', summaryKey: 'lifting_system_fit', tone: 'primary' },
  { key: 'project_supply', label: '项目供应匹配', summaryKey: 'project_supply_fit', tone: 'info' },
  { key: 'oem_odm', label: 'OEM / ODM 潜力', summaryKey: 'oem_odm_fit', tone: 'success' },
]

export type ProductOpportunitySummaryKeys = {
  total: number
  high_opportunity: number
  promising: number
  quote_ready: number
  almost_quote_ready: number
  sample_ready: number
  needs_specs: number
  lifting_system_fit: number
  project_supply_fit: number
  education_fit: number
  medical_fit: number
  oem_odm_fit: number
}

export const COMMON_QUOTE_QUESTIONS = `报价准备常见问题：
1. 需要按什么数量或体量报价？
2. 项目预计时间线是什么？
3. 最相关的产品类型是升降桌架、升降柱、桌腿，还是教育家具？
4. 是否有承重、尺寸、颜色、表面处理或认证要求？
5. 报价规划应使用哪个交付地点？`

export type ProductOpportunityBoardRow = {
  leadId: string
  companyName: string
  opportunityScore: number
  opportunityLevel: string
  projectType: string
  quoteReadiness: string
  sampleReadiness: string
  productFocus: string[]
  missingQuoteInfo: string[]
  nextProductAction: string
  nextAction: string | null
  followUpDate: string | null
  dueStatus: string | null
}

export function mapBoardRow(raw: {
  lead_id: string
  company_name: string
  opportunity_score?: number
  project_opportunity_score: number
  opportunity_level: string
  project_type: string
  quote_readiness: string
  sample_readiness: string
  recommended_product_focus?: string[]
  missing_quote_info?: string[]
  recommended_next_product_action?: string | null
  next_action?: string | null
  follow_up_date?: string | null
  due_status?: string | null
}): ProductOpportunityBoardRow {
  return {
    leadId: raw.lead_id,
    companyName: raw.company_name,
    opportunityScore: raw.opportunity_score ?? raw.project_opportunity_score,
    opportunityLevel: raw.opportunity_level,
    projectType: raw.project_type,
    quoteReadiness: raw.quote_readiness,
    sampleReadiness: raw.sample_readiness,
    productFocus: raw.recommended_product_focus ?? [],
    missingQuoteInfo: raw.missing_quote_info ?? [],
    nextProductAction: raw.recommended_next_product_action ?? '—',
    nextAction: raw.next_action ?? null,
    followUpDate: raw.follow_up_date ?? null,
    dueStatus: raw.due_status ?? null,
  }
}

export function quoteReadinessAdvice(quoteReadiness: string, sampleReadiness: string): string {
  if (quoteReadiness === 'ready') {
    return '确认最新规格后人工准备报价，并复核数量、尺寸、交付地点和认证要求。'
  }
  if (quoteReadiness === 'almost_ready') {
    return '先补齐缺失报价信息，再准备报价。可使用下方发现问题。'
  }
  if (sampleReadiness === 'ready') {
    return '可讨论样品需求和目标使用场景。'
  }
  if (sampleReadiness === 'needs_specs') {
    return '讨论样品前先确认产品尺寸、承重、表面处理和数量。'
  }
  return '先完成联系人调研并确认产品兴趣，再进入报价讨论。'
}

export function filterProductOpportunityRows(
  rows: ProductOpportunityBoardRow[],
  filter: ProductOpportunityFilterKey,
): ProductOpportunityBoardRow[] {
  if (filter === 'all') return rows
  return rows.filter((row) => {
    switch (filter) {
      case 'high_opportunity':
        return row.opportunityLevel === 'high_opportunity'
      case 'promising':
        return row.opportunityLevel === 'promising'
      case 'quote_ready':
        return row.quoteReadiness === 'ready'
      case 'almost_quote_ready':
        return row.quoteReadiness === 'almost_ready'
      case 'sample_ready':
        return row.sampleReadiness === 'ready'
      case 'needs_specs':
        return row.sampleReadiness === 'needs_specs'
      case 'lifting_system_fit':
        return row.productFocus.includes('hosun_lifting_systems')
      case 'project_supply':
        return row.productFocus.includes('project_supply')
      case 'education':
        return row.productFocus.includes('jooboo_education_furniture')
      case 'medical':
        return row.productFocus.includes('medical_workspace')
      case 'oem_odm':
        return row.productFocus.includes('oem_odm_components')
      case 'missing_quantity':
        return row.missingQuoteInfo.includes('quantity_or_volume')
      case 'missing_timeline':
        return row.missingQuoteInfo.includes('project_timeline')
      case 'missing_contact':
        return row.missingQuoteInfo.includes('contact_email_or_linkedin')
      default:
        return true
    }
  })
}

export function productFilterQueryPath(filter: ProductOpportunityFilterKey): string {
  return `/lead-intelligence?productFilter=${filter}`
}
