import { AxiosError, AxiosHeaders } from 'axios'
import { describe, expect, it } from 'vitest'
import { toAppError } from './error'

function axiosError(options: {
  code?: string
  status?: number
  detail?: unknown
  requestId?: string
  responseRequestId?: string
}) {
  const config = {
    headers: new AxiosHeaders(options.requestId ? { 'X-Request-ID': options.requestId } : {}),
  }
  return new AxiosError(
    'request failed', options.code, config, undefined,
    options.status ? {
      data: { detail: options.detail },
      status: options.status,
      statusText: 'Error',
      headers: new AxiosHeaders(options.responseRequestId ? { 'X-Request-ID': options.responseRequestId } : {}),
      config,
    } : undefined,
  )
}

describe('toAppError', () => {
  it('classifies a disconnected request as a retryable network error', () => {
    expect(toAppError(axiosError({ requestId: 'req-network' }))).toMatchObject({
      kind: 'network', message: '网络连接中断，请检查网络后重试', requestId: 'req-network', retryable: true,
    })
  })

  it('classifies request timeout separately', () => {
    expect(toAppError(axiosError({ code: 'ECONNABORTED', requestId: 'req-timeout' }))).toMatchObject({
      kind: 'timeout', message: '请求超时，请稍后重试', requestId: 'req-timeout', retryable: true,
    })
  })

  it('uses response request id and validation detail for a 422 response', () => {
    expect(toAppError(axiosError({ status: 422, detail: '日期格式不正确', requestId: 'req-client', responseRequestId: 'req-server' }))).toMatchObject({
      kind: 'validation', message: '日期格式不正确', status: 422, requestId: 'req-server', detail: '日期格式不正确', retryable: false,
    })
  })

  it('formats a structured lesson conflict', () => {
    const result = toAppError(axiosError({
      status: 409, requestId: 'req-conflict',
      detail: { error: 'time_conflict', conflicts: [{ student_name: '林晓', date: '2026-08-13', start_time: '10:00' }] },
    }))
    expect(result).toMatchObject({ kind: 'conflict', status: 409, requestId: 'req-conflict', retryable: false })
    expect(result.message).toBe('时间冲突：林晓 · 2026-08-13 10:00')
  })

  it('classifies a 503 response as a retryable server error', () => {
    expect(toAppError(axiosError({ status: 503, requestId: 'req-server' }))).toMatchObject({
      kind: 'server', status: 503, requestId: 'req-server', retryable: true,
    })
  })

  it('returns a stable unknown error for non-Axios input', () => {
    expect(toAppError(new Error('boom'))).toMatchObject({
      kind: 'unknown', message: '操作失败，请稍后再试', requestId: '', retryable: false,
    })
  })
})
