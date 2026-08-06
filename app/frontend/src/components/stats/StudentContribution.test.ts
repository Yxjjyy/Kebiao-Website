import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { StudentStatsRow } from '@/api/types'
import StudentContribution from './StudentContribution.vue'

const ranking: StudentStatsRow[] = [
  {
    student_id: 7,
    name: '林晓',
    color: '#8b5cf6',
    lesson_count: 4,
    total_hours: 4,
    total_income: 800,
    leave_count: 0,
    reschedule_count: 1,
  },
]

describe('StudentContribution', () => {
  it('renders ranked contribution and opens the selected student', async () => {
    const wrapper = mount(StudentContribution, {
      props: { ranking, currencySymbol: '¥' },
    })

    const row = wrapper.get('[data-testid="student-contribution"]')
    expect(row.attributes('aria-label')).toBe('查看林晓学生详情')
    expect(row.text()).toContain('林晓')
    expect(row.text()).toContain('¥800')
    expect(row.text()).toContain('4h')

    await row.trigger('click')
    expect(wrapper.emitted('select-student')).toEqual([[7]])
  })

  it('renders an explicit empty state', () => {
    const wrapper = mount(StudentContribution, {
      props: { ranking: [], currencySymbol: '¥' },
    })

    expect(wrapper.text()).toContain('当前周期暂无学生贡献数据')
  })
})
