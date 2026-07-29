import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import type { Lesson } from '@/api/types'
import ScheduleDashboardHeader from './ScheduleDashboardHeader.vue'

const lessons = [
  { status: '已完成' },
  { status: '待上' },
] as Lesson[]

describe('ScheduleDashboardHeader', () => {
  it('shows the greeting, teacher name and today summary', () => {
    const wrapper = mount(ScheduleDashboardHeader, {
      props: {
        displayName: '杨老师',
        avatarColor: '#7c3aed',
        todayLessons: lessons,
        now: new Date('2026-07-29T08:00:00+08:00'),
      },
    })

    expect(wrapper.text()).toContain('早上好')
    expect(wrapper.text()).toContain('杨老师')
    expect(wrapper.text()).toContain('2 节')
    expect(wrapper.text()).toContain('50%')
  })

  it('emits create from the primary action', async () => {
    const wrapper = mount(ScheduleDashboardHeader, {
      props: {
        displayName: '杨老师',
        avatarColor: '#7c3aed',
        todayLessons: [],
        now: new Date('2026-07-29T14:00:00+08:00'),
      },
    })

    await wrapper.get('[data-action="create-lesson"]').trigger('click')
    expect(wrapper.emitted('create')).toHaveLength(1)
  })
})
