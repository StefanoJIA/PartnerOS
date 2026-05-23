import { describe, expect, it } from 'vitest'
import {
  filterQueueRows,
  followUpNextAction,
  recommendChannel,
  touchpointTypeForChannel,
} from '@/constants/outreachQueue'

describe('outreachQueue', () => {
  it('recommends LinkedIn for lifting when linkedin present', () => {
    const r = recommendChannel(['lift_system_signal'], null, 'https://linkedin.com/in/x')
    expect(r.channel).toBe('linkedin_connect')
    expect(r.productFocus).toBe('hosun_lifting')
  })

  it('recommends enrich when no contact channels', () => {
    const r = recommendChannel(['medical_vertical'], null, null)
    expect(r.label).toContain('Enrich')
  })

  it('filters high score', () => {
    const rows = [
      { score: 80, segments: [], nextAction: 'x', touchCount: 0 },
      { score: 40, segments: [], nextAction: 'x', touchCount: 0 },
    ]
    expect(filterQueueRows(rows, 'high_score')).toHaveLength(1)
  })

  it('maps touchpoint types', () => {
    expect(touchpointTypeForChannel('email_intro')).toBe('catalog_sent')
  })

  it('suggests follow-up next action', () => {
    expect(followUpNextAction('linkedin_connect', 'hosun_lifting')).toContain('5 days')
  })
})
