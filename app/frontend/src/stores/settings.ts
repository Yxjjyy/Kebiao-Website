import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { settingsApi } from '@/api/settings'
import type { AppSettings, UserProfile } from '@/api/types'

const defaultSettings: AppSettings = {
  timezone: 'Asia/Shanghai',
  week_start: 1,
  currency_symbol: '¥',
  generate_weeks_ahead: 12,
  default_duration_hours: 1,
  visible_time_start: '07:00',
  visible_time_end: '22:00',
  theme: 'auto',
}

const defaultProfile: UserProfile = {
  display_name: '课表',
  avatar_color: '#4C7DFF',
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<AppSettings>({ ...defaultSettings })
  const profile = ref<UserProfile>({ ...defaultProfile })
  const loading = ref(false)

  const themeClass = computed(() => {
    if (settings.value.theme === 'dark') return 'dark'
    if (settings.value.theme === 'light') return 'light'
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  function applyTheme() {
    document.documentElement.classList.toggle('dark', themeClass.value === 'dark')
  }

  async function refresh() {
    loading.value = true
    try {
      const [settingsData, profileData] = await Promise.all([
        settingsApi.getSettings(),
        settingsApi.getProfile(),
      ])
      settings.value = settingsData
      profile.value = profileData
      applyTheme()
    } catch {
      console.warn('settings refresh failed, using defaults')
    } finally {
      loading.value = false
    }
  }

  async function saveProfile(data: Partial<UserProfile>) {
    profile.value = await settingsApi.updateProfile(data)
  }

  async function saveSettings(data: Partial<AppSettings>) {
    settings.value = await settingsApi.updateSettings(data)
    applyTheme()
  }

  return {
    settings,
    profile,
    loading,
    refresh,
    saveProfile,
    saveSettings,
    applyTheme,
  }
})
