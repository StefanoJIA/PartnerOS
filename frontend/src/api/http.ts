import axios from 'axios'

const base = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || ''

export const http = axios.create({
  baseURL: base ? `${base}/api` : '/api',
  timeout: 120000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('partneros_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('partneros_token')
      localStorage.removeItem('partneros_email')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  },
)
