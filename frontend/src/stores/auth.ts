import { defineStore } from 'pinia'
import { ref } from 'vue'
import { http } from '@/api/http'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('partneros_token'))
  const email = ref<string | null>(localStorage.getItem('partneros_email'))
  const roleName = ref<string | null>(null)
  const permissions = ref<string[]>([])

  function setSession(t: string, userEmail: string) {
    token.value = t
    email.value = userEmail
    localStorage.setItem('partneros_token', t)
    localStorage.setItem('partneros_email', userEmail)
  }

  function clear() {
    token.value = null
    email.value = null
    roleName.value = null
    permissions.value = []
    localStorage.removeItem('partneros_token')
    localStorage.removeItem('partneros_email')
  }

  async function login(userEmail: string, password: string) {
    const { data } = await http.post('/auth/login', { email: userEmail, password })
    setSession(data.access_token, userEmail)
  }

  async function fetchMe() {
    if (!token.value) return null
    const { data } = await http.get('/auth/me')
    roleName.value = data.role_name ?? null
    permissions.value = Array.isArray(data.permissions) ? data.permissions : []
    return data
  }

  function can(permission: string) {
    return permissions.value.includes('*') || permissions.value.includes(permission)
  }

  return { token, email, roleName, permissions, login, clear, fetchMe, can }
})
