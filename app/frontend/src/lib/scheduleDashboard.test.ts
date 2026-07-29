import { describe, expect, it } from 'vitest'
import type { Lesson } from '@/api/types'
import {
  findNextLesson,
  getCompletionRate,
  getGreeting,
  resolveSelectedDate,
} from './scheduleDashboard'

function lesson(id: number, date: string, startTime: string, status: Lesson['status'] = '待上'): Lesson {
  return {
    id,
    student_id: id,
    template_id: null,
    date,
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

describe('schedule dashboard helpers', () => {
  it('returns a time-appropriate greeting', () => {
    expect(getGreeting(8)).toBe('早上好')
    expect(getGreeting(14)).toBe('下午好')
    expect(getGreeting(21)).toBe('晚上好')
  })

  it('calculates completion percentage and handles an empty day', () => {
    expect(getCompletionRate([{ status: '已完成' }, { status: '待上' }])).toBe(50)
    expect(getCompletionRate([])).toBe(0)
  })

  it('selects today when it is in the week and otherwise selects the first day', () => {
    const weekDays = ['2026-07-27', '2026-07-28', '2026-07-29']
    expect(resolveSelectedDate(weekDays, '2026-07-28')).toBe('2026-07-28')
    expect(resolveSelectedDate(weekDays, '2026-08-04')).toBe('2026-07-27')
  })

  it('finds the next pending lesson and ignores completed lessons', () => {
    const lessons = [
      lesson(1, '2026-07-29', '08:00', '已完成'),
      lesson(2, '2026-07-29', '15:00'),
      lesson(3, '2026-07-30', '09:00'),
    ]

    expect(findNextLesson(lessons, new Date('2026-07-29T12:00:00+08:00'))?.id).toBe(2)
    expect(findNextLesson(lessons, new Date('2026-07-31T12:00:00+08:00'))).toBeNull()
  })
})
