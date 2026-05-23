/** 与后端 `app.constants.object_type.ObjectType` 对齐 */
export const OBJECT_TYPES = [
  'company',
  'contact',
  'lead',
  'manufacturing_partner',
  'product',
  'rfq',
  'quotation',
  'sample',
  'order',
  'field_visit',
  'field_visit_plan',
  'task',
  'interaction',
  'user',
  'file',
  'market_intelligence',
] as const

export type ObjectType = (typeof OBJECT_TYPES)[number]

const SET = new Set<string>(OBJECT_TYPES)

export function normalizeObjectType(raw: string): ObjectType {
  const v = raw.trim().toLowerCase()
  if (!SET.has(v)) {
    throw new Error(`Invalid object_type: ${raw}`)
  }
  return v as ObjectType
}
