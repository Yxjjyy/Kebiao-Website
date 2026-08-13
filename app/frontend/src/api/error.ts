import { AxiosError, isAxiosError } from 'axios'
import type { ConflictResponse } from './types'

export type AppErrorKind = 'network' | 'timeout' | 'server' | 'validation' | 'conflict' | 'unknown'

export interface AppError {
  kind: AppErrorKind
  message: string
  status?: number
  requestId: string
  detail?: unknown
  retryable: boolean
}

function headerValue(headers: unknown, name: string): string {
  if (!headers || typeof headers !== 'object') return ''
  const getter = (headers as { get?: (key: string) => unknown }).get
  const value = typeof getter === 'function'
    ? getter.call(headers, name)
    : (headers as Record<string, unknown>)[name]
      ?? (headers as Record<string, unknown>)[name.toLowerCase()]
  return typeof value === 'string' ? value : ''
}

function conflictMessage(detail: ConflictResponse): string {
  const conflicts = detail.conflicts
    .map(item => `${item.student_name} · ${item.date} ${item.start_time.slice(0, 5)}`)
    .join('；')
  return `时间冲突：${conflicts}`
}

export function toAppError(error: unknown): AppError {
  if (!isAxiosError(error)) {
    return { kind: 'unknown', message: '操作失败，请稍后再试', requestId: '', retryable: false }
  }

  const axiosError = error as AxiosError<{ detail?: string | ConflictResponse }>
  const status = axiosError.response?.status
  const detail = axiosError.response?.data?.detail
  const requestId = headerValue(axiosError.response?.headers, 'X-Request-ID')
    || headerValue(axiosError.config?.headers, 'X-Request-ID')

  if (axiosError.code === 'ECONNABORTED' || axiosError.code === 'ETIMEDOUT') {
    return { kind: 'timeout', message: '请求超时，请稍后重试', requestId, retryable: true }
  }
  if (!axiosError.response) {
    return { kind: 'network', message: '网络连接中断，请检查网络后重试', requestId, retryable: true }
  }
  if (status === 409 || (typeof detail === 'object' && detail?.error === 'time_conflict')) {
    return {
      kind: 'conflict',
      message: typeof detail === 'object' && detail.error === 'time_conflict'
        ? conflictMessage(detail)
        : typeof detail === 'string' ? detail : '数据冲突，请检查后重试',
      status,
      requestId,
      detail,
      retryable: false,
    }
  }
  if (status === 422) {
    return {
      kind: 'validation',
      message: typeof detail === 'string' ? detail : '提交内容有误，请检查后重试',
      status,
      requestId,
      detail,
      retryable: false,
    }
  }
  if (status && status >= 500) {
    return {
      kind: 'server',
      message: '服务暂时不可用，请稍后重试',
      status,
      requestId,
      detail,
      retryable: status === 502 || status === 503 || status === 504,
    }
  }
  return {
    kind: 'unknown',
    message: typeof detail === 'string' ? detail : '操作失败，请稍后再试',
    status,
    requestId,
    detail,
    retryable: false,
  }
}
