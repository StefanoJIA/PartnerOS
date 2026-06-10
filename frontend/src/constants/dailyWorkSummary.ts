/** D5.10 — end-of-day summary copy and labels. */

export const EOD_TITLE = '日终运营总结'

export const EOD_SUBTITLE =
  '复盘今日人工触达，并准备明日跟进重点。'

export const EOD_SAFETY_NOTE =
  '本总结只来自人工记录。intelliOffice 不会发送消息，也不会自动操作外部平台。'

export const EOD_DEGRADED_HINT =
  '日终总结暂不可用，请检查 backend 和数据库状态。'

export const EOD_EMPTY_HIGHLIGHTS = '该日期暂无人工动作记录。'

export const EOD_EMPTY_TOMORROW = '暂无排队中的跟进重点。'

export const EOD_COPY_SUCCESS = '总结已复制到剪贴板。'

export function todayIsoDate(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
