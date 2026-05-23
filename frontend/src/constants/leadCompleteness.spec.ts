/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it } from 'vitest'
import {
  computeCompletenessSummary,
  computeLeadCompleteness,
  filterCompletenessRows,
  type CompletenessRow,
} from './leadCompleteness'

describe('leadCompleteness', () => {
  it('scores complete lead at 80+', () => {
    const r = computeLeadCompleteness({
      companyName: 'Acme',
      companyType: 'Dealer',
      website: 'https://acme.example',
      contactName: 'Alex',
      contactTitle: 'VP',
      contactEmail: 'a@acme.example',
      contactPhone: '+1',
      segments: ['lift_system_signal'],
      intelligenceScore: 80,
      suggestedNextActions: ['Send catalog'],
      nextAction: 'Follow up',
      enrichmentStatus: 'completed',
      touchCount: 2,
    })
    expect(r.score).toBeGreaterThanOrEqual(80)
    expect(r.status).toBe('complete')
  })

  it('flags missing contact method', () => {
    const r = computeLeadCompleteness({
      companyName: 'Transfer Enterprises',
      companyType: 'Dealer',
      website: 'https://x.example',
      contactName: '—',
      segments: [],
      intelligenceScore: 30,
      nextAction: 'No next action set.',
      enrichmentStatus: 'No runs',
      touchCount: 0,
    })
    expect(r.missingFields).toContain('contact_email_or_linkedin')
  })

  it('filters needs contact research queue', () => {
    const rows: CompletenessRow[] = [
      {
        leadId: '1',
        companyName: 'A',
        score: 50,
        status: 'needs_contact_research',
        statusLabel: 'Needs Contact Research',
        missingFields: ['contact_email_or_linkedin'],
        recommendedResearchAction: 'Add email',
        segments: [],
        nextAction: '—',
        lastTouch: '—',
      },
      {
        leadId: '2',
        companyName: 'B',
        score: 85,
        status: 'complete',
        statusLabel: 'Complete',
        missingFields: [],
        recommendedResearchAction: 'Generate draft',
        segments: ['lift_system_signal'],
        nextAction: 'Wait',
        lastTouch: 'sent',
      },
    ]
    const filtered = filterCompletenessRows(rows, 'needs_contact_research')
    expect(filtered).toHaveLength(1)
    expect(filtered[0].companyName).toBe('A')
  })

  it('summary counts missing website', () => {
    const rows: CompletenessRow[] = [
      {
        leadId: '1',
        companyName: 'A',
        score: 40,
        status: 'incomplete',
        statusLabel: 'Incomplete',
        missingFields: ['website'],
        recommendedResearchAction: 'Add website',
        segments: [],
        nextAction: '—',
        lastTouch: '—',
      },
    ]
    const s = computeCompletenessSummary(rows)
    expect(s.missingWebsite).toBe(1)
  })
})
