import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { ComparisonStats, LeaveItem, RangeStats, StudentStatsRow } from '@/api/types'
import StatsPanel from './StatsPanel.vue'

const range: RangeStats = {
  from_date: '2026-07-01',
  to_date: '2026-07-07',
  granularity: 'day',
  total_income: 800,
  total_hours: 4,
  total_lessons: 5,
  completed_lessons: 4,
  pending_lessons: 0,
  leave_count: 1,
  reschedule_count: 0,
  active_students: 1,
  buckets: [{ bucket: '2026-07-01', income: 800, hours: 4, lesson_count: 4 }],
}

const comparison: ComparisonStats = {
  period: 'week',
  current_income: 800,
  previous_income: 600,
  income_growth_pct: 33.3,
  current_hours: 4,
  previous_hours: 3,
  hours_growth_pct: 33.3,
  current_lessons: 4,
  previous_lessons: 3,
}

const ranking: StudentStatsRow[] = [{
  student_id: 7,
  name: '林晓',
  color: '#8b5cf6',
  lesson_count: 4,
  total_hours: 4,
  total_income: 800,
  leave_count: 1,
  reschedule_count: 0,
}]

const leaveItems: LeaveItem[] = [{
  id: 3,
  student_id: 7,
  student_name: '林晓',
  date: '2026-07-03',
  start_time: '10:00',
  duration_hours: 1,
  status: '请假',
  note: null,
}]

const baseProps = {
  today: null,
  range,
  ranking,
  comparison,
  leaveItems,
  statRange: 'week',
  currencySymbol: '¥',
  statsOffset: 0,
  statsPeriodLabel: '7月1日 — 7月7日',
  isCurrentPeriod: true,
  loading: false,
  error: '',
}

describe('StatsPanel', () => {
  it('composes the statistics workspace and forwards interactions', async () => {
    const wrapper = mount(StatsPanel, { props: baseProps })

    expect(wrapper.text()).toContain('数据统计')
    expect(wrapper.text()).toContain('学生贡献')
    expect(wrapper.text()).toContain('待关注事项')
    expect(wrapper.text()).toContain('7月1日 — 7月7日')

    await wrapper.get('[data-range="month"]').trigger('click')
    expect(wrapper.emitted('change-range')).toEqual([['month']])

    await wrapper.get('[data-testid="student-contribution"]').trigger('click')
    expect(wrapper.emitted('select-student')).toEqual([[7]])
  })

  it('shows an initial loading skeleton', () => {
    const wrapper = mount(StatsPanel, {
      props: { ...baseProps, range: null, loading: true },
    })

    expect(wrapper.find('[data-testid="stats-skeleton"]').exists()).toBe(true)
  })

  it('offers retry when loading statistics fails', async () => {
    const wrapper = mount(StatsPanel, {
      props: { ...baseProps, range: null, error: '统计数据加载失败' },
    })

    expect(wrapper.text()).toContain('统计数据加载失败')
    await wrapper.get('[data-action="retry-stats"]').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})
