import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { Lesson } from '@/api/types'
import MobileLessonActionsSheet from './MobileLessonActionsSheet.vue'

function lesson(status: Lesson['status']): Lesson {
  return {
    id: 8,
    student_id: 3,
    template_id: null,
    date: '2026-07-29',
    start_time: '15:00',
    duration_hours: 1.5,
    status,
    price: 300,
    note: '核心训练',
    rescheduled_from_id: null,
    rescheduled_to_id: null,
    created_at: '',
    updated_at: '',
    student: { id: 3, name: '林沐', color: '#7c3aed' },
  }
}

describe('MobileLessonActionsSheet', () => {
  it('shows pending lesson actions and emits complete with the lesson', async () => {
    const pending = lesson('待上')
    const wrapper = mount(MobileLessonActionsSheet, {
      props: { lesson: pending, currencySymbol: '¥' },
    })

    expect(wrapper.text()).toContain('完成课程')
    expect(wrapper.text()).toContain('标记请假')
    expect(wrapper.text()).toContain('调整时间')
    expect(wrapper.text()).toContain('编辑详情')
    expect(wrapper.text()).toContain('加入日历')
    expect(wrapper.text()).toContain('删除课程')

    await wrapper.get('[data-action="complete"]').trigger('click')
    expect(wrapper.emitted('complete')).toEqual([[pending]])
  })

  it('shows restore instead of pending-only actions for a completed lesson', () => {
    const wrapper = mount(MobileLessonActionsSheet, {
      props: { lesson: lesson('已完成'), currencySymbol: '¥' },
    })

    expect(wrapper.text()).toContain('恢复待上')
    expect(wrapper.text()).not.toContain('完成课程')
    expect(wrapper.text()).not.toContain('标记请假')
    expect(wrapper.text()).not.toContain('调整时间')
  })

  it('emits close from both the close button and backdrop', async () => {
    const wrapper = mount(MobileLessonActionsSheet, {
      props: { lesson: lesson('待上'), currencySymbol: '¥' },
    })

    await wrapper.get('[data-action="close"]').trigger('click')
    await wrapper.get('[data-testid="action-sheet-backdrop"]').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(2)
  })
})
