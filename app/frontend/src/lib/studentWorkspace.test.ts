import { describe, expect, it } from 'vitest'
import type { Student, Template } from '@/api/types'
import {
  filterStudents,
  formatRepeatInterval,
  normalizeSelectedStudentId,
  sortTemplates,
} from './studentWorkspace'

const students = [
  { id: 1, name: '林沐', phone: '13800138000' },
  { id: 2, name: '周宁', phone: '13900139000' },
] as Student[]

describe('student workspace helpers', () => {
  it('filters students by name or phone and ignores surrounding whitespace', () => {
    expect(filterStudents(students, '')).toEqual(students)
    expect(filterStudents(students, ' 林 ')).toEqual([students[0]])
    expect(filterStudents(students, '139')).toEqual([students[1]])
  })

  it('keeps a valid selection and falls back to the first student', () => {
    expect(normalizeSelectedStudentId(students, 2)).toBe(2)
    expect(normalizeSelectedStudentId(students, 99)).toBe(1)
    expect(normalizeSelectedStudentId([], 1)).toBeNull()
  })

  it('sorts templates by weekday and time without mutating the input', () => {
    const templates = [
      { id: 1, day_of_week: 2, start_time: '09:00' },
      { id: 2, day_of_week: 0, start_time: '16:00' },
      { id: 3, day_of_week: 0, start_time: '09:00' },
    ] as Template[]

    expect(sortTemplates(templates).map((item) => item.id)).toEqual([3, 2, 1])
    expect(templates.map((item) => item.id)).toEqual([1, 2, 3])
  })

  it('formats repeat intervals', () => {
    expect(formatRepeatInterval(1)).toBe('每周')
    expect(formatRepeatInterval(2)).toBe('隔周')
    expect(formatRepeatInterval(4)).toBe('每 4 周')
  })
})
