import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { RangeStats } from '@/api/types'
import StatsTrendChart from './StatsTrendChart.vue'

const range = {
  from_date: '2026-07-01',
  to_date: '2026-07-03',
  granularity: 'day',
  total_income: 500,
  total_hours: 4,
  total_lessons: 3,
  completed_lessons: 2,
  pending_lessons: 1,
  leave_count: 0,
  reschedule_count: 0,
  active_students: 2,
  buckets: [
    { bucket: '2026-07-01', income: 200, hours: 1, lesson_count: 1 },
    { bucket: '2026-07-02', income: 300, hours: 3, lesson_count: 2 },
  ],
} satisfies RangeStats

describe('StatsTrendChart', () => {
  it('shows an explicit empty state', () => {
    const wrapper = mount(StatsTrendChart, {
      props: { range: { ...range, buckets: [] }, currencySymbol: '¥' },
    })

    expect(wrapper.text()).toContain('当前周期暂无趋势数据')
  })

  it('renders income and hours paths with accessible trend points', () => {
    const wrapper = mount(StatsTrendChart, {
      props: { range, currencySymbol: '¥' },
    })

    expect(wrapper.find('[data-testid="income-line"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="hours-line"]').exists()).toBe(true)
    const point = wrapper.findAll('[data-testid="trend-point"]')[0]
    expect(point.attributes('aria-label')).toContain('2026-07-01')
    expect(point.attributes('aria-label')).toContain('¥200')
    expect(point.attributes('tabindex')).toBe('0')
  })

  it('switches the emphasized mobile metric', async () => {
    const wrapper = mount(StatsTrendChart, {
      props: { range, currencySymbol: '¥' },
    })

    expect(wrapper.get('[data-testid="income-line"]').attributes('data-active')).toBe('true')
    await wrapper.get('[data-testid="metric-hours-toggle"]').trigger('click')
    expect(wrapper.get('[data-testid="hours-line"]').attributes('data-active')).toBe('true')
    expect(wrapper.get('[data-testid="income-line"]').attributes('data-active')).toBe('false')
  })
})
