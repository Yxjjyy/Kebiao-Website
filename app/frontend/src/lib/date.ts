import {
  addDays,
  addMonths,
  addWeeks,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  isSameDay,
  parseISO,
  startOfMonth,
  startOfWeek,
} from 'date-fns'
import { zhCN } from 'date-fns/locale'

export function getTodayIso() {
  return format(new Date(), 'yyyy-MM-dd')
}

export function getWeekRange(base = new Date(), weekStartsOn: 0 | 1 = 1) {
  const start = startOfWeek(base, { weekStartsOn })
  const end = endOfWeek(base, { weekStartsOn })
  return { start, end }
}

export function getWeekDays(base = new Date(), weekStartsOn: 0 | 1 = 1) {
  const { start, end } = getWeekRange(base, weekStartsOn)
  return eachDayOfInterval({ start, end })
}

export function getMonthRange(base = new Date()) {
  return {
    start: startOfMonth(base),
    end: endOfMonth(base),
  }
}

export function toIsoDate(value: Date) {
  return format(value, 'yyyy-MM-dd')
}

export function formatWeekday(value: Date | string) {
  return format(typeof value === 'string' ? parseISO(value) : value, 'EEEE', { locale: zhCN })
}

export function formatShortDate(value: Date | string) {
  return format(typeof value === 'string' ? parseISO(value) : value, 'M月d日')
}

export function formatMonthDay(value: Date | string) {
  return format(typeof value === 'string' ? parseISO(value) : value, 'MM-dd')
}

export function formatHourMinute(value: string) {
  return value.slice(0, 5)
}

export function isToday(value: string) {
  return isSameDay(parseISO(value), new Date())
}

export function addDaysIso(value: string, amount: number) {
  return toIsoDate(addDays(parseISO(value), amount))
}

export function getOffsetWeekRange(offset: number, weekStartsOn: 0 | 1 = 1) {
  const base = addWeeks(new Date(), offset)
  const start = startOfWeek(base, { weekStartsOn })
  const end = endOfWeek(base, { weekStartsOn })
  return { start, end }
}

export function getOffsetMonthRange(offset: number) {
  const base = addMonths(new Date(), offset)
  return {
    start: startOfMonth(base),
    end: endOfMonth(base),
  }
}
