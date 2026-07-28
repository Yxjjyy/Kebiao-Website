import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', () => {
  const token = ref('ok')
  const verifying = ref(false)

  const isAuthenticated = computed(() => true)

  function loadFromStorage() {}

  function setToken(_next: string) {}

  function clear() {}

  async function verify() {
    return true
  }

  return {
    token,
    verifying,
    isAuthenticated,
    loadFromStorage,
    setToken,
    clear,
    verify,
  }
})
