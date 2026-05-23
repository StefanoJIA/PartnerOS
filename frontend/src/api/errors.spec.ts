import { describe, expect, it } from 'vitest'
import axios from 'axios'
import { BACKEND_HINT, DB_HINT, formatApiError, isDatabaseError } from './errors'

describe('formatApiError', () => {
  it('maps 500 to database hint', () => {
    const err = new axios.AxiosError('fail', '500', undefined, undefined, {
      status: 500,
      data: { detail: 'Internal Server Error' },
      statusText: 'Internal Server Error',
      headers: {},
      config: {} as never,
    })
    expect(formatApiError(err, 'fallback')).toBe(DB_HINT)
    expect(isDatabaseError(err)).toBe(true)
  })

  it('maps network errors to backend hint', () => {
    const err = new axios.AxiosError('Network Error', 'ERR_NETWORK')
    expect(formatApiError(err, 'fallback')).toBe(BACKEND_HINT)
    expect(isDatabaseError(err)).toBe(false)
  })

  it('returns fallback for unknown errors', () => {
    expect(formatApiError(new Error('x'), 'custom fallback')).toBe('custom fallback')
  })
})
