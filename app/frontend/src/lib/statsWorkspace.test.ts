import { describe, expect, it } from 'vitest'
import type { RangeStats } from '@/api/types'
import {
  calculateCompletionRate,
  contributionPercent,
  fillTrendPoints,
  formatGrowth,
  visibleAttentionItems,
} from './statsWorkspace'

const range: RangeStats = {
  from_date: '2026-07-01',
  to_date: '2026-07-03',
  granularity: 'day',
  total_income: 200,
  total_hours: 2,
  total_lessons: 2,
  completed_lessons: 1,
  pending_lessons: 1,
  leave_count: 0,
  reschedule_count: 0,
  active_students: 1,
  buckets: [
    { bucket: '2026-07-01', income: 200, hours: 1, lesson_count: 1 },
    { bucket: '2026-07-03', income: 0, hours: 1, lesson_count: 1 },
  ],
}

describe('statistics workspace helpers', () => {
  it('calculates completion rate from active lessons and handles a zero denominator', () => {
    expect(calculateCompletionRate(6, 2)).toBe(75)
    expect(calculateCompletionRate(0, 0)).toBe(0)
  })

  it('formats comparable growth without inventing zero-baseline growth', () => {
    expect(formatGrowth(12.45)).toEqual({ label: '较上期 ↑12.5%', tone: 'positive' })
    expect(formatGrowth(-4)).toEqual({ label: '较上期 ↓4.0%', tone: 'negative' })
    expect(formatGrowth(0)).toEqual({ label: '与上期持平', tone: 'neutral' })
    expect(formatGrowth(null)).toEqual({ label: '上期暂无数据', tone: 'muted' })
  })

  it('fills missing daily trend points without mutating source buckets', () => {
    const points = fillTrendPoints(range)

    expect(points.map((point) => point.bucket)).toEqual([
      '2026-07-01',
      '2026-07-02',
      '2026-07-03',
    ])
    expect(points[1]).toEqual({
      bucket: '2026-07-02',
      income: 0,
      hours: 0,
      lesson_count: 0,
    })
    expect(range.buckets).toHaveLength(2)
  })

  it('keeps natural weekly buckets in chronological order', () => {
    expect(fillTrendPoints({
      ...range,
      granularity: 'week',
      buckets: [
        { bucket: '2026-07-13', income: 20, hours: 1, lesson_count: 1 },
        { bucket: '2026-07-06', income: 10, hours: 1, lesson_count: 1 },
      ],
    }).map((point) => point.bucket)).toEqual(['2026-07-06', '2026-07-13'])
  })

  it('normalizes contribution and mobile attention defaults', () => {
    expect(contributionPercent(250, 500)).toBe(50)
    expect(contributionPercent(800, 500)).toBe(100)
    expect(contributionPercent(0, 0)).toBe(0)
    expect(visibleAttentionItems([1, 2, 3, 4], false)).toEqual([1, 2, 3])
    expect(visibleAttentionItems([1, 2, 3, 4], true)).toHaveLength(4)
  })
})
