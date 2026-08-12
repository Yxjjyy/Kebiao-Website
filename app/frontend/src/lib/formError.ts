import { AxiosError } from 'axios'
import type { ConflictResponse } from '@/api/types'

export function parseFormError(
  error: unknown,
  fallback = '操作失败，请稍后再试',
): string {
  const data = error instanceof AxiosError
    ? error.response?.data
    : (error as { response?: { data?: unknown } })?.response?.data
  const detail = (data as { detail?: string | ConflictResponse } | undefined)?.detail

  if (typeof detail === 'string') return detail
  if (detail?.error === 'time_conflict') {
    const conflicts = detail.conflicts
      .map((item) => `${item.student_name} · ${item.date} ${item.start_time.slice(0, 5)}`)
      .join('；')
    return `时间冲突：${conflicts}`
  }
  return fallback
}
