import { AxiosError } from 'axios'
import { describe, expect, it } from 'vitest'
import { parseFormError } from './formError'

describe('parseFormError', () => {
  it('formats structured lesson conflicts', () => {
    const error = new AxiosError('conflict', '409', undefined, undefined, {
      data: {
        detail: {
          error: 'time_conflict',
          conflicts: [
            {
              id: 1,
              student_id: 2,
              student_name: '林晓',
              date: '2026-08-10',
              start_time: '10:00',
              duration_hours: 1,
            },
          ],
        },
      },
      status: 409,
      statusText: 'Conflict',
      headers: {},
      config: {} as never,
    })

    expect(parseFormError(error)).toContain('林晓 · 2026-08-10 10:00')
  })

  it('uses server detail and a stable fallback', () => {
    expect(parseFormError({ response: { data: { detail: '日期无效' } } })).toBe('日期无效')
    expect(parseFormError(new Error('boom'))).toBe('操作失败，请稍后再试')
  })
})
