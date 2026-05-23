/** Pilot touchpoint presets (frontend-only; no schema change). */

export const TOUCHPOINT_TYPE_PRESETS = [
  { label: 'Contact research', value: 'contact_research' },
  { label: 'LinkedIn connect note', value: 'linkedin_connect_note' },
  { label: 'Catalog sent', value: 'catalog_sent' },
  { label: 'Quotation follow-up', value: 'quotation_follow_up' },
  { label: 'Sample discussion', value: 'sample_discussion' },
  { label: 'Meeting proposed', value: 'meeting_proposed' },
  { label: 'Waiting for reply', value: 'waiting_for_reply' },
  { label: 'Not a fit', value: 'not_a_fit' },
  { label: 'General follow-up', value: 'follow_up' },
] as const

export const NEXT_ACTION_SUGGESTIONS = [
  'Send HOSUN adjustable frame catalog',
  'Schedule intro call — lifting columns',
  'Request project BOQ / floor plan',
  'Follow up on sample timeline',
  'Send JOOBOO education line sheet',
  'Confirm healthcare compliance needs',
  'Waiting for customer reply',
  'Mark as not a fit — archive',
] as const

export const CHANNEL_PRESETS = [
  { label: 'Manual research', value: 'manual_research' },
  { label: 'Phone', value: 'phone' },
  { label: 'Email', value: 'email' },
  { label: 'LinkedIn', value: 'linkedin' },
  { label: 'Visit', value: 'visit' },
  { label: 'Video call', value: 'video' },
] as const
