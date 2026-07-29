import type { Student, Template } from '@/api/types'

export function filterStudents(students: Student[], query: string): Student[] {
  const normalized = query.trim().toLocaleLowerCase()
  if (!normalized) return students
  return students.filter((student) =>
    student.name.toLocaleLowerCase().includes(normalized)
    || student.phone?.toLocaleLowerCase().includes(normalized)
  )
}

export function normalizeSelectedStudentId(
  students: Student[],
  selectedId: number | null
): number | null {
  if (!students.length) return null
  if (selectedId !== null && students.some((student) => student.id === selectedId)) return selectedId
  return students[0].id
}

export function sortTemplates(templates: Template[]): Template[] {
  return [...templates].sort((left, right) =>
    left.day_of_week - right.day_of_week || left.start_time.localeCompare(right.start_time)
  )
}

export function formatRepeatInterval(interval = 1): string {
  if (interval === 1) return '每周'
  if (interval === 2) return '隔周'
  return `每 ${interval} 周`
}
