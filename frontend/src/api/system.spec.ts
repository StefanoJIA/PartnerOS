import { describe, expect, it } from 'vitest'

/** Pure helper for portal readiness display labels (D5.2.9). */
export function automaticSendingLabel(enabled: boolean | undefined): string {
  return enabled ? 'Enabled' : 'Disabled'
}

describe('portal integration helpers', () => {
  it('automaticSendingLabel returns Disabled when false or undefined', () => {
    expect(automaticSendingLabel(false)).toBe('Disabled')
    expect(automaticSendingLabel(undefined)).toBe('Disabled')
  })

  it('automaticSendingLabel returns Enabled only when true', () => {
    expect(automaticSendingLabel(true)).toBe('Enabled')
  })
})
