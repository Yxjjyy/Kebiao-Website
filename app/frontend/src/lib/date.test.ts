import { describe, expect, it } from 'vitest'
import { getBusinessTodayIso, getMonthRange, getWeekRange, toIsoDate } from './date'

describe('business date boundaries', () => {
  it('derives the date from the configured timezone', () => {
    const instant = new Date('2026-08-13T16:30:00.000Z')
    expect(getBusinessTodayIso('UTC', instant)).toBe('2026-08-13')
    expect(getBusinessTodayIso('Asia/Shanghai', instant)).toBe('2026-08-14')
  })

  it('supports Monday and Sunday week starts across a year boundary', () => {
    const value = new Date(2026, 0, 1)
    expect(toIsoDate(getWeekRange(value, 1).start)).toBe('2025-12-29')
    expect(toIsoDate(getWeekRange(value, 0).start)).toBe('2025-12-28')
  })

  it('handles leap-year month ends', () => {
    expect(toIsoDate(getMonthRange(new Date(2024, 1, 10)).end)).toBe('2024-02-29')
  })
})
