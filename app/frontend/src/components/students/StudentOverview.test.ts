import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { StudentDetail } from '@/api/types'
import StudentOverview from './StudentOverview.vue'

const student = {
  id: 1,
  name: '林沐',
  color: '#7c3aed',
  hourly_rate: 300,
  phone: '13800138000',
  note: '专注核心训练',
  archived: 0,
  created_at: '',
  updated_at: '',
  stats: {
    month_income: 3600,
    month_hours: 12,
    month_lesson_count: 10,
    month_leave_count: 1,
  },
  template_count: 2,
} satisfies StudentDetail

describe('StudentOverview', () => {
  it('renders identity, contact details and monthly metrics', () => {
    const wrapper = mount(StudentOverview, {
      props: { student, loading: false, error: '', currencySymbol: '¥' },
    })
    const text = wrapper.text()

    expect(text).toContain('林沐')
    expect(text).toContain('13800138000')
    expect(text).toContain('专注核心训练')
    expect(text).toContain('¥3600')
    expect(text).toContain('12')
    expect(text).toContain('10')
    expect(text).toContain('1')
    expect(text).toContain('2')
  })

  it('shows explicit placeholders for missing contact information', () => {
    const wrapper = mount(StudentOverview, {
      props: {
        student: { ...student, phone: null, note: null },
        loading: false,
        error: '',
        currencySymbol: '¥',
      },
    })

    expect(wrapper.text()).toContain('未填写电话')
    expect(wrapper.text()).toContain('暂无备注')
  })

  it('emits retry from the local error state', async () => {
    const wrapper = mount(StudentOverview, {
      props: { student: null, loading: false, error: '学生详情加载失败', currencySymbol: '¥' },
    })

    await wrapper.get('[data-action="retry-student-detail"]').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })

  it('emits edit with the student id', async () => {
    const wrapper = mount(StudentOverview, {
      props: { student, loading: false, error: '', currencySymbol: '¥' },
    })

    await wrapper.get('[data-action="edit-student"]').trigger('click')
    expect(wrapper.emitted('edit-student')).toEqual([[1]])
  })
})
