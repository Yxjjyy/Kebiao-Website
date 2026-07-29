import type { Lesson } from '@/api/types'

export function getGreeting(hour: number): string {
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
}

export function getCompletionRate(lessons: Pick<Lesson, 'status'>[]): number {
  if (!lessons.length) return 0
  const completed = lessons.filter((lesson) => lesson.status === '已完成').length
  return Math.round((completed / lessons.length) * 100)
}

export function resolveSelectedDate(weekDays: string[], todayIso: string): string {
  if (weekDays.includes(todayIso)) return todayIso
  return weekDays[0] ?? todayIso
}

export function findNextLesson(lessons: Lesson[], now: Date): Lesson | null {
  return [...lessons]
    .filter((lesson) => lesson.status === '待上')
    .filter((lesson) => new Date(`${lesson.date}T${lesson.start_time}:00`).getTime() >= now.getTime())
    .sort((left, right) =>
      `${left.date}T${left.start_time}`.localeCompare(`${right.date}T${right.start_time}`)
    )[0] ?? null
}
