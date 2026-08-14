import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { settingsApi } from '@/api/settings'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(import.meta.env.VITE_ACCESS_TOKEN || 'yang')
  const verifying = ref(false)
  const authenticated = ref(true)

  const isAuthenticated = computed(() => authenticated.value)

  function loadFromStorage() {
    authenticated.value = true
  }

  function setToken(_next: string) {
    authenticated.value = true
  }

  function clear() {
    authenticated.value = false
  }

  async function verify() {
    if (verifying.value) return true
    verifying.value = true
    try {
      await settingsApi.verifyToken()
      authenticated.value = true
      return true
    } catch {
      authenticated.value = false
      return false
    } finally {
      verifying.value = false
    }
  }

  return {
    token,
    verifying,
    authenticated,
    isAuthenticated,
    loadFromStorage,
    setToken,
    clear,
    verify,
  }
})
