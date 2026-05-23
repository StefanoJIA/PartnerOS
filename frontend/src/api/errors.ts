/** Map API errors to operator-friendly messages (D5.2.13). */

import axios from 'axios'

const DB_HINT =
  'Database unavailable. Start Docker DB (docker compose up -d db) or check DATABASE_URL in backend/.env.'

const BACKEND_HINT =
  'Backend not reachable. Start uvicorn and run: python scripts/check_backend_runtime.py'

export function formatApiError(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const status = err.response?.status
    const detail = err.response?.data?.detail
    if (status === 401) return 'Session expired. Please sign in again.'
    if (status === 404) return 'Resource not found. Restart backend if a new route was added.'
    if (status === 400 && typeof detail === 'string') return detail
    if (status === 500 || status === 503) return DB_HINT
    if (!err.response) return BACKEND_HINT
  }
  return fallback
}

export function isDatabaseError(err: unknown): boolean {
  if (axios.isAxiosError(err)) {
    const status = err.response?.status
    return status === 500 || status === 503
  }
  return false
}

export { DB_HINT, BACKEND_HINT }
