import { api } from './client'

export const exportApi = {
  async downloadXlsx(from: string, to: string) {
    const response = await api.get<Blob>('/export/xlsx', {
      params: { from, to },
      responseType: 'blob',
    })
    return response.data
  },
}
