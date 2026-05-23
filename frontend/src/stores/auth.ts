import { defineStore } from 'pinia'
import { ref } from 'vue'
import { http } from '@/api/http'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('partneros_token'))
  const email = ref<string | null>(localStorage.getItem('partneros_email'))

  function setSession(t: string, userEmail: string) {
    token.value = t
    email.value = userEmail
    localStorage.setItem('partneros_token', t)
    localStorage.setItem('partneros_email', userEmail)
  }

  function clear() {
    token.value = null
    email.value = null
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
    return data
  }

  return { token, email, login, clear, fetchMe }
})
