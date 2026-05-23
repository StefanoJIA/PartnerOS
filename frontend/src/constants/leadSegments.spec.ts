import { describe, expect, it } from 'vitest'
import {
  SEGMENT_FILTER_OPTIONS,
  segmentLabel,
  segmentTagType,
  priorityHint,
} from '@/constants/leadSegments'

describe('leadSegments', () => {
  it('maps known segment slugs to pilot labels', () => {
    expect(segmentLabel('lift_system_signal')).toBe('Lifting System Signal')
    expect(segmentLabel('medical_vertical')).toBe('Medical / Healthcare Vertical')
    expect(segmentLabel('oem_odm_fit')).toBe('OEM / ODM Signal')
  })

  it('exposes pilot segment filters', () => {
    expect(SEGMENT_FILTER_OPTIONS.map((o) => o.key)).toContain('lift_system_signal')
    expect(SEGMENT_FILTER_OPTIONS[0].key).toBe('all')
  })

  it('scores priority hints', () => {
    expect(priorityHint(75, null)).toContain('High fit')
    expect(priorityHint(30, 'High')).toContain('Priority')
  })

  it('tags lift segment as success', () => {
    expect(segmentTagType('lift_system_signal')).toBe('success')
  })
})
