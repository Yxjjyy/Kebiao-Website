import { api } from './client'
import type { Lesson, LessonStatus } from './types'

export const lessonsApi = {
  list: (from: string, to: string, studentId?: number) =>
    api
      .get<Lesson[]>('/lessons', { params: { from, to, student_id: studentId } })
      .then((r) => r.data),

  create: (data: {
    student_id: number
    date: string
    start_time: string
    duration_hours: number
    note?: string | null
  }) => api.post<Lesson>('/lessons', data).then((r) => r.data),

  update: (
    id: number,
    data: Partial<{
      date: string
      start_time: string
      duration_hours: number
      status: LessonStatus
      note: string | null
    }>
  ) => api.patch<Lesson>(`/lessons/${id}`, data).then((r) => r.data),

  reschedule: (
    id: number,
    data: {
      new_date: string
      new_start_time: string
      new_duration_hours?: number
      note?: string | null
    }
  ) =>
    api
      .post<{ old: Lesson; new: Lesson }>(`/lessons/${id}/reschedule`, data)
      .then((r) => r.data),

  cancel: (id: number, note?: string) =>
    api.post<Lesson>(`/lessons/${id}/cancel`, { note }).then((r) => r.data),

  restore: (id: number) =>
    api.post<Lesson>(`/lessons/${id}/restore`).then((r) => r.data),

  bulk: (data: {
    ids: number[]
    action: 'complete' | 'cancel' | 'restore' | 'delete'
    note?: string | null
  }) => api.post<{ affected: number }>('/lessons/bulk', data).then((r) => r.data),

  remove: (id: number) => api.delete(`/lessons/${id}`),
}
