import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import LessonTimeFields from './LessonTimeFields.vue'

describe('LessonTimeFields', () => {
  it('renders grouped accessible inputs and updates each value', async () => {
    const wrapper = mount(LessonTimeFields, {
      props: {
        date: '2026-08-10',
        startTime: '10:00',
        durationHours: 1,
        dateLabel: '新日期',
      },
    })

    expect(wrapper.text()).toContain('新日期')
    await wrapper.get('[data-field="lesson-date"]').setValue('2026-08-11')
    await wrapper.get('[data-field="lesson-start-time"]').setValue('11:30')
    await wrapper.get('[data-field="lesson-duration"]').setValue('1.5')

    expect(wrapper.emitted('update:date')).toEqual([['2026-08-11']])
    expect(wrapper.emitted('update:startTime')).toEqual([['11:30']])
    expect(wrapper.emitted('update:durationHours')).toEqual([[1.5]])
  })
})
