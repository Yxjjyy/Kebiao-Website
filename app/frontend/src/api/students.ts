import { api } from './client'
import type { Student, StudentDetail } from './types'

export const studentsApi = {
  list: (archived = false) =>
    api.get<Student[]>('/students', { params: { archived } }).then((r) => r.data),

  get: (id: number) => api.get<StudentDetail>(`/students/${id}`).then((r) => r.data),

  create: (data: {
    name: string
    color: string
    hourly_rate: number
    phone?: string | null
    note?: string | null
  }) => api.post<Student>('/students', data).then((r) => r.data),

  update: (id: number, data: Partial<Student>, recalcMode = 'today') =>
    api
      .patch<{ student: Student; affected_future_lessons: number }>(`/students/${id}`, data, { params: { recalc_mode: recalcMode } })
      .then((r) => r.data),

  archive: (id: number) => api.post<Student>(`/students/${id}/archive`).then((r) => r.data),

  unarchive: (id: number) => api.post<Student>(`/students/${id}/unarchive`).then((r) => r.data),

  remove: (id: number) => api.delete(`/students/${id}`),
}
