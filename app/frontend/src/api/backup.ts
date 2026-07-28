import { api } from './client'

export const backupApi = {
  async download() {
    const response = await api.get<Blob>('/backup', { responseType: 'blob' })
    return response.data
  },

  async restore(file: File) {
    const form = new FormData()
    form.append('file', file)
    return api
      .post<{ ok: boolean; restored_to: string; old_saved_at: string }>('/restore', form, {
        headers: {
          'X-Confirm-Restore': 'yes',
        },
      })
      .then((r) => r.data)
  },
}
