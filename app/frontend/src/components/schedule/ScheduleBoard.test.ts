import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Lesson } from '@/api/types'
import ScheduleBoard from './ScheduleBoard.vue'

function lesson(id: number, date: string, name: string): Lesson {
  return {
    id,
    student_id: id,
    template_id: null,
    date,
    start_time: id === 1 ? '09:30' : '15:00',
    duration_hours: 1,
    status: '待上',
    price: 200,
    note: null,
    rescheduled_from_id: null,
    rescheduled_to_id: null,
    created_at: '',
    updated_at: '',
    student: { id, name, color: '#7c3aed' },
  }
}

function mountBoard(lessons: Lesson[]) {
  return mount(ScheduleBoard, {
    global: { plugins: [createPinia()] },
    props: {
      lessons,
      currencySymbol: '¥',
      selectedLessonId: null,
      selectedLessonIds: [],
      visibleStart: '08:00',
      visibleEnd: '18:00',
      weekStart: new Date('2026-07-29T10:00:00+08:00'),
    },
  })
}

describe('ScheduleBoard mobile agenda', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-07-29T10:00:00+08:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('defaults to today and switches the visible course list by date', async () => {
    const wrapper = mountBoard([
      lesson(1, '2026-07-29', '林沐'),
      lesson(2, '2026-07-30', '周宁'),
    ])

    expect(wrapper.get('[data-testid="mobile-course-list"]').text()).toContain('林沐')
    expect(wrapper.get('[data-testid="mobile-course-list"]').text()).not.toContain('周宁')

    await wrapper.get('[data-date="2026-07-30"]').trigger('click')
    expect(wrapper.get('[data-testid="mobile-course-list"]').text()).toContain('周宁')
    expect(wrapper.get('[data-testid="mobile-course-list"]').text()).not.toContain('林沐')
  })

  it('opens the action sheet when a mobile course card is clicked', async () => {
    const current = lesson(1, '2026-07-29', '林沐')
    const wrapper = mountBoard([current])

    await wrapper.get('[data-testid="mobile-course-card"]').trigger('click')
    expect(wrapper.emitted('open-mobile-actions')).toEqual([[current]])
  })

  it('shows a clear empty state for a date without lessons', async () => {
    const wrapper = mountBoard([lesson(1, '2026-07-29', '林沐')])

    await wrapper.get('[data-date="2026-07-30"]').trigger('click')
    expect(wrapper.get('[data-testid="mobile-course-list"]').text()).toContain('今天没有课程')
  })
})
