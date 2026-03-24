import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getMe } from '@/api/auth'
import type { UserInfo, LoginPayload } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserInfo | null>(null)
  const sessionExpired = ref(false)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function clearToken() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  function notifySessionExpired() {
    if (token.value) {
      clearToken()
      sessionExpired.value = true
    }
  }

  function dismissSessionExpired() {
    sessionExpired.value = false
  }

  async function login(payload: LoginPayload) {
    const res = await apiLogin(payload)
    setToken(res.data.access_token)
    await fetchMe()
  }

  async function logout() {
    clearToken()
  }

  async function fetchMe() {
    try {
      const res = await getMe()
      user.value = res.data
    } catch {
      clearToken()
    }
  }

  async function initFromStorage() {
    if (token.value && !user.value) {
      await fetchMe()
    }
  }

  const isSuperAdmin = computed(() => user.value?.role === 0)

  return { token, user, sessionExpired, isSuperAdmin, login, logout, fetchMe, initFromStorage, notifySessionExpired, dismissSessionExpired }
})
