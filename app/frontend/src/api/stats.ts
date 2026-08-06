import { api } from './client'
import type {
  ComparisonStats,
  LeaveItem,
  RangeStats,
  StudentStatsRow,
  TodayStats,
} from './types'

function comparison(period: 'week' | 'month'): Promise<ComparisonStats>
function comparison(
  from: string,
  to: string,
  period: 'day' | 'week' | 'month',
): Promise<ComparisonStats>
function comparison(
  fromOrPeriod: string,
  to?: string,
  period?: 'day' | 'week' | 'month',
) {
  const params = to && period
    ? { from: fromOrPeriod, to, period }
    : { period: fromOrPeriod }
  return api
    .get<ComparisonStats>('/stats/comparison', { params })
    .then((response) => response.data)
}

export const statsApi = {
  today: () => api.get<TodayStats>('/stats/today').then((r) => r.data),

  range: (from: string, to: string, granularity: 'day' | 'week' | 'month' = 'day') =>
    api
      .get<RangeStats>('/stats/range', { params: { from, to, granularity } })
      .then((r) => r.data),

  students: (from: string, to: string) =>
    api
      .get<StudentStatsRow[]>('/stats/students', { params: { from, to } })
      .then((r) => r.data),

  leave: (from: string, to: string) =>
    api.get<LeaveItem[]>('/stats/leave', { params: { from, to } }).then((r) => r.data),

  comparison,
}
