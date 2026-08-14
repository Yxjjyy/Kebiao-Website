import { toAppError } from '@/api/error'

export function parseFormError(
  error: unknown,
  fallback = '操作失败，请稍后再试',
): string {
  const legacyDetail = (error as { response?: { data?: { detail?: unknown } } } | null)
    ?.response?.data?.detail
  if (typeof legacyDetail === 'string') return legacyDetail
  if (legacyDetail && typeof legacyDetail === 'object') {
    const message = (legacyDetail as { message?: unknown }).message
    if (typeof message === 'string') return message
  }

  const parsed = toAppError(error)
  return parsed.kind === 'unknown' && parsed.message === '操作失败，请稍后再试'
    ? fallback
    : parsed.message
}
