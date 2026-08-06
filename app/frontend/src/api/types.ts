export type LessonStatus = '待上' | '已完成' | '请假' | '已调课'

export interface Student {
  id: number
  name: string
  color: string
  hourly_rate: number
  phone: string | null
  note: string | null
  archived: number
  created_at: string
  updated_at: string
}

export interface StudentDetail extends Student {
  stats: {
    month_income: number
    month_hours: number
    month_lesson_count: number
    month_leave_count: number
  }
  template_count: number
}

export interface Template {
  id: number
  student_id: number
  day_of_week: number
  start_time: string
  duration_hours: number
  effective_from: string
  effective_to: string | null
  repeat_interval?: number
}

export interface Lesson {
  id: number
  student_id: number
  template_id: number | null
  date: string
  start_time: string
  duration_hours: number
  status: LessonStatus
  price: number
  note: string | null
  rescheduled_from_id: number | null
  rescheduled_to_id: number | null
  created_at: string
  updated_at: string
  student?: { id: number; name: string; color: string } | null
}

export interface TodayStats {
  date: string
  total_lessons: number
  expected_income: number
  earned_income: number
  total_hours: number
  lessons: Lesson[]
}

export interface RangeBucket {
  bucket: string
  income: number
  hours: number
  lesson_count: number
}

export interface RangeStats {
  from_date: string
  to_date: string
  granularity: string
  total_income: number
  total_hours: number
  total_lessons: number
  completed_lessons: number
  pending_lessons: number
  leave_count: number
  reschedule_count: number
  active_students: number
  buckets: RangeBucket[]
}

export interface StudentStatsRow {
  student_id: number
  name: string
  color: string
  lesson_count: number
  total_hours: number
  total_income: number
  leave_count: number
  reschedule_count: number
}

export interface LeaveItem {
  id: number
  student_id: number
  student_name: string
  date: string
  start_time: string
  duration_hours: number
  status: string
  note: string | null
}

export interface ComparisonStats {
  period: string
  current_income: number
  previous_income: number
  income_growth_pct: number | null
  current_hours: number
  previous_hours: number
  hours_growth_pct: number | null
  current_lessons: number
  previous_lessons: number
}

export interface AppSettings {
  timezone: string
  week_start: number
  currency_symbol: string
  generate_weeks_ahead: number
  default_duration_hours: number
  visible_time_start: string
  visible_time_end: string
  theme: 'auto' | 'light' | 'dark'
}

export interface UserProfile {
  display_name: string
  avatar_color: string
}

export interface ConflictDetail {
  id: number
  student_id: number
  student_name: string
  start_time: string
  duration_hours: number
  date: string
}

export interface ConflictResponse {
  error: 'time_conflict'
  conflicts: ConflictDetail[]
}
