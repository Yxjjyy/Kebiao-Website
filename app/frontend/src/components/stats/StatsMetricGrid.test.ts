import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { ComparisonStats, RangeStats } from '@/api/types'
import StatsMetricGrid from './StatsMetricGrid.vue'

const range = {
  from_date: '2026-07-01',
  to_date: '2026-07-31',
  granularity: 'week',
  total_income: 1200,
  total_hours: 10,
  total_lessons: 8,
  completed_lessons: 6,
  pending_lessons: 2,
  leave_count: 2,
  reschedule_count: 1,
  active_students: 4,
  buckets: [],
} satisfies RangeStats

const comparison = {
  period: 'month',
  current_income: 1200,
  previous_income: 1000,
  income_growth_pct: 20,
  current_hours: 10,
  previous_hours: 8,
  hours_growth_pct: 25,
  current_lessons: 8,
  previous_lessons: 7,
} satisfies ComparisonStats

describe('StatsMetricGrid', () => {
  it('renders the four decision metrics and comparison context', () => {
    const wrapper = mount(StatsMetricGrid, {
      props: { range, comparison, currencySymbol: '¥' },
    })

    expect(wrapper.text()).toContain('实际收入')
    expect(wrapper.text()).toContain('¥1200')
    expect(wrapper.text()).toContain('有效课时')
    expect(wrapper.text()).toContain('10h')
    expect(wrapper.text()).toContain('课程完成率')
    expect(wrapper.text()).toContain('75%')
    expect(wrapper.text()).toContain('已完成 6 / 共 8 节')
    expect(wrapper.text()).toContain('活跃学生')
    expect(wrapper.text()).toContain('4')
    expect(wrapper.text()).toContain('较上期 ↑20.0%')
  })

  it('explains an empty completion denominator', () => {
    const wrapper = mount(StatsMetricGrid, {
      props: {
        range: {
          ...range,
          total_lessons: 0,
          completed_lessons: 0,
          pending_lessons: 0,
          leave_count: 0,
        },
        comparison: null,
        currencySymbol: '¥',
      },
    })

    expect(wrapper.get('[data-testid="metric-completion"]').text()).toContain('暂无课程')
  })
})
