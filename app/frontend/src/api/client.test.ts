import { AxiosError, AxiosHeaders, type AxiosAdapter, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { describe, expect, it, vi } from 'vitest'
import { createApiClient } from './client'

function response(config: AxiosRequestConfig, status = 200): AxiosResponse {
  return { data: {}, status, statusText: String(status), headers: {}, config: config as never }
}

function failure(config: AxiosRequestConfig, status?: number, code?: string) {
  return new AxiosError(
    'failed', code, config as never, undefined,
    status ? response(config, status) : undefined,
  )
}

describe('API retry policy', () => {
  it.each([
    ['network', undefined, undefined],
    ['timeout', undefined, 'ECONNABORTED'],
    ['bad gateway', 502, undefined],
    ['unavailable', 503, undefined],
    ['gateway timeout', 504, undefined],
  ])('retries GET %s twice with one request ID', async (_label, status, code) => {
    const requestIds: string[] = []
    const adapter: AxiosAdapter = vi.fn(async (config) => {
      requestIds.push(String(AxiosHeaders.from(config.headers).get('X-Request-ID') ?? ''))
      if (requestIds.length < 3) throw failure(config, status, code)
      return response(config)
    })
    const sleep = vi.fn<(delay: number) => Promise<void>>(async () => undefined)
    const client = createApiClient({ adapter, requestId: () => 'req-fixed', sleep })

    await expect(client.get('/lessons')).resolves.toMatchObject({ status: 200 })
    expect(adapter).toHaveBeenCalledTimes(3)
    expect(requestIds).toEqual(['req-fixed', 'req-fixed', 'req-fixed'])
    expect(sleep.mock.calls.map(([delay]) => delay)).toEqual([150, 300])
  })

  it.each(['post', 'patch', 'delete'] as const)('never retries %s writes', async (method) => {
    const adapter = vi.fn(async (config: AxiosRequestConfig) => {
      throw failure(config, 503)
    })
    const client = createApiClient({ adapter, requestId: () => 'req-write', sleep: async () => undefined })

    await expect(client.request({ method, url: '/lessons', data: {} })).rejects.toBeInstanceOf(AxiosError)
    expect(adapter).toHaveBeenCalledOnce()
  })

  it('does not retry an actively canceled GET', async () => {
    const adapter = vi.fn(async (config: AxiosRequestConfig) => {
      throw failure(config, undefined, 'ERR_CANCELED')
    })
    const client = createApiClient({ adapter, requestId: () => 'req-cancel', sleep: async () => undefined })

    await expect(client.get('/lessons')).rejects.toMatchObject({ code: 'ERR_CANCELED' })
    expect(adapter).toHaveBeenCalledOnce()
  })
})
