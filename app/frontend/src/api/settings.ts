import { api } from './client'
import type { AppSettings, UserProfile } from './types'

export const settingsApi = {
  getSettings: () => api.get<AppSettings>('/settings').then((r) => r.data),

  updateSettings: (data: Partial<AppSettings>) =>
    api.patch<AppSettings>('/settings', data).then((r) => r.data),

  getProfile: () => api.get<UserProfile>('/profile').then((r) => r.data),

  updateProfile: (data: Partial<UserProfile>) =>
    api.patch<UserProfile>('/profile', data).then((r) => r.data),
}
