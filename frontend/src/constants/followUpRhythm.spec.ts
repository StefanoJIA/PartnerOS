import { describe, expect, it } from 'vitest'
import {
  classifyFollowUpCategories,
  computeDailySummary,
  filterByRhythmCategory,
  primaryStatusBadge,
} from '@/constants/followUpRhythm'
import { filterQueueRows, NO_NEXT_ACTION } from '@/constants/outreachQueue'

const baseRow = {
  score: 55,
  segments: ['lift_system_signal'],
  nextAction: NO_NEXT_ACTION,
  touchCount: 0,
  lastTouch: '—',
  lastTouchDate: null,
  contactEmail: 'a@test.com',
  linkedinUrl: null,
  enrichmentStatus: 'No runs',
  companyWebsite: null,
}

describe('followUpRhythm', () => {
  it('classifies needs first outreach', () => {
    const cats = classifyFollowUpCategories(baseRow)
    expect(cats).toContain('needs_first_outreach')
  })

  it('classifies waiting for reply after manual send', () => {
    const cats = classifyFollowUpCategories({
      ...baseRow,
      touchCount: 1,
      lastTouch: '[manually_sent=true] channel=email_intro',
      nextAction: 'Wait for reply — follow up in 5 days',
    })
    expect(cats).toContain('waiting_for_reply')
  })

  it('computes daily summary counts', () => {
    const summary = computeDailySummary([
      { ...baseRow, companyName: 'A' },
      {
        ...baseRow,
        companyName: 'B',
        score: 80,
        segments: ['project_based_furniture'],
      },
    ] as Array<typeof baseRow & { companyName: string }>)
    expect(summary.total).toBe(2)
    expect(summary.high_priority).toBeGreaterThanOrEqual(1)
  })

  it('filters today focus', () => {
    const rows = [
      { ...baseRow, companyName: 'A' },
      {
        ...baseRow,
        companyName: 'B',
        segments: [],
        touchCount: 5,
        nextAction: 'Archived — no action',
      },
    ]
    const focused = filterByRhythmCategory(rows, 'today_focus')
    expect(focused.length).toBeGreaterThanOrEqual(1)
  })

  it('integrates operation filter in filterQueueRows', () => {
    const rows = [
      { ...baseRow, score: 80, segments: ['project_based_furniture'] },
      { ...baseRow, score: 20, segments: [] },
    ]
    expect(filterQueueRows(rows, 'high_priority').length).toBeGreaterThanOrEqual(1)
  })

  it('primary badge orders high priority first', () => {
    expect(primaryStatusBadge(['needs_first_outreach', 'high_priority'])).toBe('high_priority')
  })
})
