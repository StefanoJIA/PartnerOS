export const ORDER_STATUS_LABELS: Record<string, string> = {
  pending_customer_confirmation: '待客户确认',
  confirmed: '已确认',
  internal_review: '内部复核',
  supplier_confirmation_pending: '待供应商确认',
  supplier_confirmed: '供应商已确认',
  production_pending: '待生产',
  in_production: '生产中',
  ready_to_ship: '待发运',
  shipped: '已发运',
  delivered: '已交付',
  on_hold: '暂停',
  cancelled: '已取消',
}

export const QUOTE_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  prepared: '已准备',
  sent: '已发送',
  accepted: '已接受',
  rejected: '已拒绝',
  expired: '已过期',
  converted: '已转订单',
  converted_to_order: '已转订单',
}

export const FEEDBACK_STATUS_LABELS: Record<string, string> = {
  new: '新反馈',
  in_review: '复核中',
  responded: '已回应',
  resolved: '已解决',
  closed: '已关闭',
}

export const FEEDBACK_PRIORITY_LABELS: Record<string, string> = {
  low: '低',
  normal: '普通',
  high: '高',
  urgent: '紧急',
}

export const SHIPMENT_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  planned: '已计划',
  booked: '已订舱',
  in_transit: '运输中',
  shipped: '已发运',
  delivered: '已交付',
  delayed: '延误',
  cancelled: '已取消',
}

export const PRODUCTION_STATUS_LABELS: Record<string, string> = {
  planned: '已计划',
  pending: '待开始',
  in_progress: '进行中',
  completed: '已完成',
  blocked: '阻塞',
  delayed: '延误',
  cancelled: '已取消',
}

export const SUPPLIER_CONFIRMATION_LABELS: Record<string, string> = {
  pending: '待确认',
  confirmed: '已确认',
  partially_confirmed: '部分确认',
  needs_clarification: '需澄清',
  rejected: '已拒绝',
}

export const RESOURCE_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
}

export const PARTNER_ONBOARDING_STAGE_LABELS: Record<string, string> = {
  discovery: '发现阶段',
  product_mapping: '产品映射',
  quote_ready: '报价就绪',
  portal_ready: 'Portal 就绪',
  demo_ready: '演示就绪',
  active_partner: '活跃伙伴',
  paused: '暂停',
}

export const MARKET_SIGNAL_LABELS: Record<string, string> = {
  adjustable_desk_frames: '升降桌架',
  desk_legs: '桌腿',
  lifting_columns: '升降柱',
  education_furniture: '教育家具',
  project_furniture: '项目制家具',
  other: '其他关注方向',
}

export const PORTAL_READINESS_LABELS: Record<string, string> = {
  done: '已完成',
  ready: '就绪',
  ready_for_operator: '运营可接手',
  needs_operator_action: '需运营处理',
  blocked: '阻塞',
  missing: '缺失',
  check: '需检查',
}

export const DUE_STATUS_LABELS: Record<string, string> = {
  overdue: '已逾期',
  due_today: '今日到期',
  due_soon: '即将到期',
  waiting_reply: '等待回复',
  ready_for_outreach: '可触达',
  needs_contact_research: '需联系人调研',
  missing_enrichment: '需补全资料',
}

export const ACTIVITY_BADGE_LABELS: Record<string, string> = {
  'Manual sent': '已人工发送',
  'Contact research': '联系人调研',
  'Follow-up scheduled': '已安排跟进',
}

export function zhLabel(map: Record<string, string>, value: string | null | undefined, fallback = '未设置'): string {
  if (!value) return fallback
  return map[value] || value
}
