import type { Lesson } from '@/api/types'

export function generateICS(lesson: Lesson, studentName: string): string {
  const fmt = (d: string, t: string) => {
    const date = d.replace(/-/g, '')
    const time = t.replace(/:/g, '') + '00'
    return date + 'T' + time
  }
  const start = fmt(lesson.date, lesson.start_time)

  const [startH, startM] = lesson.start_time.split(':').map(Number)
  const endMinTotal = startH * 60 + startM + lesson.duration_hours * 60
  const extraDays = Math.floor(endMinTotal / 1440)
  const eh = Math.floor((endMinTotal % 1440) / 60)
  const em = endMinTotal % 60
  const endDate = extraDays > 0
    ? new Date(new Date(lesson.date).getTime() + extraDays * 86400000).toISOString().slice(0, 10)
    : lesson.date
  const end = fmt(endDate, `${String(eh).padStart(2, '0')}:${String(em).padStart(2, '0')}`)

  const uid = `lesson-${lesson.id}@kebiao`
  const now = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z'

  return [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//kebiao//CN',
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${now}`,
    `DTSTART:${start}`,
    `DTEND:${end}`,
    `SUMMARY:${studentName}`,
    `DESCRIPTION:${lesson.note || '课程提醒'}`,
    'BEGIN:VALARM',
    'TRIGGER:-PT5M',
    'ACTION:DISPLAY',
    'DESCRIPTION:5分钟后开始上课',
    'END:VALARM',
    'END:VEVENT',
    'END:VCALENDAR',
  ].join('\r\n')
}

export function downloadICS(lesson: Lesson, studentName: string) {
  const ics = generateICS(lesson, studentName)
  const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `lesson-${lesson.id}.ics`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
