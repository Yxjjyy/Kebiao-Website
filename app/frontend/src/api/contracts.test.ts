import type { AxiosAdapter, AxiosRequestConfig, AxiosResponse } from 'axios'
import { afterEach, describe, expect, it } from 'vitest'
import { api } from './client'
import { toAppError } from './error'
import { lessonsApi } from './lessons'
import { statsApi } from './stats'
import { studentsApi } from './students'

function response(config: AxiosRequestConfig, data: unknown, status = 200): AxiosResponse {
  return { data, status, statusText: String(status), headers: {}, config: config as never }
}

afterEach(() => {
  api.defaults.adapter = undefined
})

describe('frontend API contracts', () => {
  it('parses student, lesson and statistics payloads from the backend contract', async () => {
    const adapter: AxiosAdapter = async (config) => {
      if (config.url === '/students') return response(config, [{ id: 1, name: '林晓', color: '#8b5cf6', hourly_rate: 200 }])
      if (config.url === '/lessons') return response(config, [{ id: 8, student_id: 1, date: '2026-08-13', status: '待上' }])
      if (config.url === '/stats/range') return response(config, { total_income: 200, total_hours: 1, completed_lessons: 1, pending_lessons: 0 })
      throw new Error(`unexpected ${config.url}`)
    }
    api.defaults.adapter = adapter

    await expect(studentsApi.list()).resolves.toMatchObject([{ id: 1, name: '林晓' }])
    await expect(lessonsApi.list('2026-08-13', '2026-08-13')).resolves.toMatchObject([{ id: 8, status: '待上' }])
    await expect(statsApi.range('2026-08-13', '2026-08-13')).resolves.toMatchObject({ total_income: 200, total_hours: 1 })
  })

  it('maps the structured conflict contract with the echoed request ID', () => {
    const error = {
      isAxiosError: true,
      config: { headers: { 'X-Request-ID': 'req-client' } },
      response: {
        status: 409,
        headers: { 'X-Request-ID': 'req-server' },
        data: { detail: { error: 'time_conflict', conflicts: [{ student_name: '林晓', date: '2026-08-13', start_time: '10:00' }] } },
      },
    }

    expect(toAppError(error)).toMatchObject({
      kind: 'conflict', status: 409, requestId: 'req-server', retryable: false,
      message: '时间冲突：林晓 · 2026-08-13 10:00',
    })
  })
})
