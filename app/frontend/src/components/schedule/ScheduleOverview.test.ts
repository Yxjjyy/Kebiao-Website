import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { Lesson } from '@/api/types'
import ScheduleOverview from './ScheduleOverview.vue'

function lesson(id: number, startTime: string, status: Lesson['status'] = '待上'): Lesson {
  return {
    id,
    student_id: id,
    template_id: null,
    date: '2026-07-29',
    start_time: startTime,
    duration_hours: 1,
    status,
    price: 200,
    note: null,
    rescheduled_from_id: null,
    rescheduled_to_id: null,
    created_at: '',
    updated_at: '',
    student: { id, name: `学生 ${id}`, color: '#7c3aed' },
  }
}

describe('ScheduleOverview', () => {
  it('shows today totals and the next pending lesson', () => {
    const wrapper = mount(ScheduleOverview, {
      props: {
        todayLessons: [lesson(1, '09:00', '已完成'), lesson(2, '15:00')],
        activeStudentCount: 18,
        now: new Date('2026-07-29T12:00:00+08:00'),
      },
    })

    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('50%')
    expect(wrapper.text()).toContain('学生 2')
    expect(wrapper.text()).toContain('18')
  })

  it('shows an explicit empty next-lesson state', () => {
    const wrapper = mount(ScheduleOverview, {
      props: {
        todayLessons: [lesson(1, '09:00', '已完成')],
        activeStudentCount: 1,
        now: new Date('2026-07-29T12:00:00+08:00'),
      },
    })

    expect(wrapper.text()).toContain('今日课程已结束')
  })
})
