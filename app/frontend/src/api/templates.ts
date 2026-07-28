import { api } from './client'
import type { Template } from './types'

export const templatesApi = {
  list: (studentId?: number) =>
    api
      .get<Template[]>('/templates', { params: { student_id: studentId } })
      .then((r) => r.data),

  create: (data: Omit<Template, 'id'>) =>
    api
      .post<{ template: Template; generated_lessons: number }>('/templates', data)
      .then((r) => r.data),

  update: (
    id: number,
    data: Partial<Omit<Template, 'id' | 'student_id'>> & {
      apply_mode?: 'future_only' | 'from_date' | 'template_only' | 'update_all'
      apply_from_date?: string
    }
  ) =>
    api
      .patch<{ template: Template; regenerated_lessons: number }>(
        `/templates/${id}`,
        data
      )
      .then((r) => r.data),

  remove: (id: number, cancelFuture = true) =>
    api
      .delete<{ cancelled_lessons: number }>(`/templates/${id}`, {
        params: { cancel_future: cancelFuture },
      })
      .then((r) => r.data),
}
