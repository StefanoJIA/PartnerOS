/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it } from 'vitest'
import { filterByDueQueue, quickFollowUpDates } from './followUpScheduling'

describe('followUpScheduling', () => {
  it('quick buttons compute dates', () => {
    const q = quickFollowUpDates(new Date(2026, 4, 23))
    expect(q.in5Days).toBe('2026-05-28')
    expect(q.tomorrow).toBe('2026-05-24')
  })

  it('filters overdue rows', () => {
    const rows = [
      { leadId: '1', dueStatus: 'overdue' },
      { leadId: '2', dueStatus: 'scheduled' },
    ]
    const out = filterByDueQueue(rows, 'overdue', {})
    expect(out).toHaveLength(1)
    expect(out[0].leadId).toBe('1')
  })
})
