import { describe, expect, it } from 'vitest'

/** Pure helper for portal readiness display labels (D5.2.9). */
export function automaticSendingLabel(enabled: boolean | undefined): string {
  return enabled ? 'Enabled' : 'Disabled'
}

/** D5.2.10 — portal consumer mock display helpers */
export function portalConsumerSafetyOk(automaticSendingEnabled: boolean | undefined): boolean {
  return automaticSendingEnabled === false
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

describe('portal consumer mock helpers', () => {
  it('portalConsumerSafetyOk is true only when automatic sending disabled', () => {
    expect(portalConsumerSafetyOk(false)).toBe(true)
    expect(portalConsumerSafetyOk(undefined)).toBe(false)
    expect(portalConsumerSafetyOk(true)).toBe(false)
  })
})
