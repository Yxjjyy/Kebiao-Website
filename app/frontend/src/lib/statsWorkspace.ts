import type { RangeBucket, RangeStats } from '@/api/types'

export type GrowthTone = 'positive' | 'negative' | 'neutral' | 'muted'

export function calculateCompletionRate(
  completed: number,
  pending: number,
  leave: number,
): number {
  const denominator = completed + pending + leave
  return denominator ? Math.round((completed / denominator) * 100) : 0
}

export function formatGrowth(value: number | null): {
  label: string
  tone: GrowthTone
} {
  if (value === null) return { label: '上期暂无数据', tone: 'muted' }
  const rounded = Math.round((Math.abs(value) + Number.EPSILON) * 10) / 10
  if (value > 0) return { label: `较上期 ↑${rounded.toFixed(1)}%`, tone: 'positive' }
  if (value < 0) return { label: `较上期 ↓${rounded.toFixed(1)}%`, tone: 'negative' }
  return { label: '与上期持平', tone: 'neutral' }
}

export function contributionPercent(value: number, maximum: number): number {
  if (maximum <= 0) return 0
  return Math.round(Math.max(0, Math.min(1, value / maximum)) * 100)
}

export function visibleAttentionItems<T>(items: T[], expanded: boolean): T[] {
  return expanded ? items : items.slice(0, 3)
}

function emptyBucket(bucket: string): RangeBucket {
  return { bucket, income: 0, hours: 0, lesson_count: 0 }
}

function localIsoDate(value: Date): string {
  return [
    value.getFullYear(),
    String(value.getMonth() + 1).padStart(2, '0'),
    String(value.getDate()).padStart(2, '0'),
  ].join('-')
}

export function fillTrendPoints(range: RangeStats): RangeBucket[] {
  const ordered = [...range.buckets].sort((left, right) =>
    left.bucket.localeCompare(right.bucket),
  )
  if (range.granularity !== 'day') return ordered

  const byDate = new Map(ordered.map((bucket) => [bucket.bucket, bucket]))
  const cursor = new Date(`${range.from_date}T00:00:00`)
  const end = new Date(`${range.to_date}T00:00:00`)
  const result: RangeBucket[] = []
  while (cursor <= end) {
    const iso = localIsoDate(cursor)
    result.push(byDate.get(iso) ?? emptyBucket(iso))
    cursor.setDate(cursor.getDate() + 1)
  }
  return result
}
