import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import { getSessionToken, setSessionToken } from '@/lib/session'

export const useAuthStore = defineStore('auth', () => {
  const authenticated = ref<boolean | null>(null)
  const verifying = ref(false)

  const isAuthenticated = computed(() => authenticated.value === true)

  async function verify(): Promise<boolean> {
    if (verifying.value) return authenticated.value === true
    if (!getSessionToken()) {
      authenticated.value = false
      return false
    }
    verifying.value = true
    try {
      await authApi.me()
      authenticated.value = true
      return true
    } catch {
      setSessionToken(null)
      authenticated.value = false
      return false
    } finally {
      verifying.value = false
    }
  }

  async function login(username: string, password: string): Promise<void> {
    const { token } = await authApi.login(username, password)
    setSessionToken(token)
    authenticated.value = true
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch {
      // 忽略登出接口异常，本地一律清除
    }
    setSessionToken(null)
    authenticated.value = false
  }

  return {
    authenticated,
    verifying,
    isAuthenticated,
    verify,
    login,
    logout,
  }
})
