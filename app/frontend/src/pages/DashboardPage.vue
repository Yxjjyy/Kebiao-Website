<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import SettingsPanel from '@/components/layout/SettingsPanel.vue'
import CreateLessonModal from '@/components/schedule/CreateLessonModal.vue'
import DayView from '@/components/schedule/DayView.vue'
import LessonEditModal from '@/components/schedule/LessonEditModal.vue'
import MonthView from '@/components/schedule/MonthView.vue'
import MobileLessonActionsSheet from '@/components/schedule/MobileLessonActionsSheet.vue'
import RescheduleLessonModal from '@/components/schedule/RescheduleLessonModal.vue'
import RescheduleModeModal from '@/components/schedule/RescheduleModeModal.vue'
import ScheduleBoard from '@/components/schedule/ScheduleBoard.vue'
import ScheduleDashboardHeader from '@/components/schedule/ScheduleDashboardHeader.vue'
import ScheduleOverview from '@/components/schedule/ScheduleOverview.vue'
import StatsPanel from '@/components/stats/StatsPanel.vue'
import StudentOverview from '@/components/students/StudentOverview.vue'
import TemplateManager from '@/components/students/TemplateManager.vue'
import StudentsPanel from '@/components/students/StudentsPanel.vue'
import StudentFormModal from '@/components/students/StudentFormModal.vue'
import TemplateFormModal from '@/components/students/TemplateFormModal.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ErrorNotice from '@/components/ui/ErrorNotice.vue'
import { isCancel } from 'axios'
import { toAppError, type AppError } from '@/api/error'
import { exportApi } from '@/api/export'
import { lessonsApi } from '@/api/lessons'
import { statsApi } from '@/api/stats'
import { studentsApi } from '@/api/students'
import { templatesApi } from '@/api/templates'
import type {
  ComparisonStats,
  LeaveItem,
  Lesson,
  RangeStats,
  Student,
  StudentDetail,
  StudentStatsRow,
  Template,
  TodayStats,
} from '@/api/types'
import { addDays, format } from 'date-fns'
import { getOffsetMonthRange, getOffsetWeekRange, getWeekRange, toIsoDate } from '@/lib/date'
import { normalizeSelectedStudentId } from '@/lib/studentWorkspace'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()
const route = useRoute()
const router = useRouter()
const activeTab = ref<string>('schedule')
const loading = ref(false)
const statsLoading = ref(false)
const statsError = ref<AppError | null>(null)
const dashboardError = ref<AppError | null>(null)
let dashboardRequestId = 0
let statsRequestId = 0

const lessons = ref<Lesson[]>([])
const students = ref<Student[]>([])
const todayStats = ref<TodayStats | null>(null)
const rangeStats = ref<RangeStats | null>(null)
const comparisonStats = ref<ComparisonStats | null>(null)
const ranking = ref<StudentStatsRow[]>([])
const templates = ref<Template[]>([])
const selectedStudentDetail = ref<StudentDetail | null>(null)
const studentDetailLoading = ref(false)
const studentDetailError = ref<AppError | null>(null)
let studentDetailRequestId = 0
const templatesLoading = ref(false)
const templatesError = ref<AppError | null>(null)
let templatesRequestId = 0
const selectedLesson = ref<Lesson | null>(null)
const selectedStudentId = ref<number | null>(null)
const statRange = ref<'today' | 'week' | 'month'>('month')
const statsOffset = ref(0)
const leaveItems = ref<LeaveItem[]>([])
const quickCreate = ref<{ date: string; start_time: string } | null>(null)
const scheduleError = ref('')
const bulkSelectedIds = ref<number[]>([])
type PendingDangerAction =
  | { kind: 'lesson-delete'; lesson: Lesson }
  | { kind: 'lesson-cancel'; lesson: Lesson }
  | { kind: 'bulk-delete'; lessonIds: number[] }
  | { kind: 'bulk-cancel'; lessonIds: number[] }
  | null
const pendingDangerAction = ref<PendingDangerAction>(null)
const dangerSubmitting = ref(false)
const weekOffset = ref(0)
const refreshKey = ref(0)
const viewMode = ref<'week' | 'month' | 'day'>('week')
const selectedDay = ref('')
const monthDate = ref(new Date())

const showCreateLesson = ref(false)
const showStudentForm = ref(false)
const studentFormMode = ref<'create' | 'edit'>('create')
const editingStudent = ref<Student | null>(null)
const showTemplateForm = ref(false)
const templateFormMode = ref<'create' | 'edit'>('create')
const editingTemplate = ref<Template | null>(null)
const showRescheduleMode = ref(false)
const pendingMovePayload = ref<{ lesson: Lesson; date: string; start_time: string } | null>(null)
const showRescheduleLesson = ref(false)
const rescheduleTarget = ref<Lesson | null>(null)
const mobileActionLesson = ref<Lesson | null>(null)

const currentWeekStart = computed(() => addDays(new Date(), weekOffset.value * 7))

const weekRangeLabel = computed(() => {
  const range = getWeekRange(currentWeekStart.value, (settingsStore.settings.week_start as 0 | 1) ?? 1)
  return `${format(range.start, 'M月d日')} - ${format(range.end, 'M月d日')}`
})

const currencySymbol = computed(() => settingsStore.settings.currency_symbol)
const displayName = computed(() => settingsStore.profile.display_name || '教师')
const avatarColor = computed(() => settingsStore.profile.avatar_color || '#7c3aed')
const todayLessons = computed(() =>
  todayStats.value?.lessons ?? lessons.value.filter((lesson) => lesson.date === toIsoDate(new Date()))
)
const statRangeLabel = computed(() =>
  statRange.value === 'today' ? '今日' : statRange.value === 'week' ? '本周' : '本月'
)

const statsPeriodLabel = computed(() => {
  const range = getStatsRange(statsOffset.value)
  if (statRange.value === 'today') {
    return format(range.start, 'M月d日')
  }
  if (statRange.value === 'week') {
    return `${format(range.start, 'M月d日')} - ${format(range.end, 'M月d日')}`
  }
  return format(range.start, 'yyyy年M月')
})

const isCurrentStatsPeriod = computed(() => statsOffset.value === 0 && statRange.value !== 'today')

function loadError(error: unknown, fallback: string): AppError {
  const parsed = toAppError(error)
  return parsed.kind === 'unknown'
    ? { ...parsed, message: fallback, retryable: true }
    : parsed
}

function tabFromPath(path: string): 'schedule' | 'students' | 'stats' | 'settings' {
  if (path.startsWith('/students')) return 'students'
  if (path.startsWith('/stats')) return 'stats'
  if (path.startsWith('/settings')) return 'settings'
  return 'schedule'
}

function prevWeek() { weekOffset.value-- }
function nextWeek() { weekOffset.value++ }
function goToToday() { weekOffset.value = 0; monthDate.value = new Date(); selectedDay.value = '' }

function prevStatsPeriod() { statsOffset.value-- }
function nextStatsPeriod() { if (statsOffset.value < 0) statsOffset.value++ }
function goToCurrentStatsPeriod() { statsOffset.value = 0 }

function handleViewChange(mode: 'week' | 'month' | 'day') {
  viewMode.value = mode
  if (mode === 'month') {
    monthDate.value = addDays(new Date(), weekOffset.value * 7)
  }
}

function handleDayClick(dateIso: string) {
  selectedDay.value = dateIso
  viewMode.value = 'day'
}

function handlePrevMonth() {
  monthDate.value = new Date(monthDate.value.getFullYear(), monthDate.value.getMonth() - 1, 1)
}

function handleNextMonth() {
  monthDate.value = new Date(monthDate.value.getFullYear(), monthDate.value.getMonth() + 1, 1)
}

function handlePrevDay() {
  const d = new Date(selectedDay.value || toIsoDate(addDays(new Date(), weekOffset.value * 7)))
  selectedDay.value = toIsoDate(addDays(d, -1))
}

function handleNextDay() {
  const d = new Date(selectedDay.value || toIsoDate(addDays(new Date(), weekOffset.value * 7)))
  selectedDay.value = toIsoDate(addDays(d, 1))
}

function getStatsRange(offset = 0) {
  const today = new Date()
  if (statRange.value === 'today') {
    return { start: today, end: today, granularity: 'day' as const }
  }
  if (statRange.value === 'week') {
    const week = getOffsetWeekRange(offset, (settingsStore.settings.week_start as 0 | 1) ?? 1)
    return { start: week.start, end: week.end > today ? today : week.end, granularity: 'day' as const }
  }
  const month = getOffsetMonthRange(offset)
  return { start: month.start, end: month.end > today ? today : month.end, granularity: 'week' as const }
}

async function loadDashboard() {
  const requestId = ++dashboardRequestId
  loading.value = true
  dashboardError.value = null
  try {
    const week = getWeekRange(currentWeekStart.value, (settingsStore.settings.week_start as 0 | 1) ?? 1)
    const [lessonRows, studentRows, today] = await Promise.all([
      lessonsApi.list(toIsoDate(week.start), toIsoDate(week.end)),
      studentsApi.list(false),
      statsApi.today(),
    ])
    if (requestId !== dashboardRequestId) return
    lessons.value = lessonRows
    students.value = studentRows
    todayStats.value = today
    const requestedStudentId = route.path.startsWith('/students')
      ? Number(route.query.student) || selectedStudentId.value
      : selectedStudentId.value
    selectedStudentId.value = normalizeSelectedStudentId(studentRows, requestedStudentId)
    refreshKey.value++
  } catch (error) {
    if (requestId === dashboardRequestId && !isCancel(error)) {
      dashboardError.value = loadError(error, '数据加载失败，请检查网络后重试')
    }
  } finally {
    if (requestId === dashboardRequestId) loading.value = false
  }
}

async function loadStatistics() {
  const requestId = ++statsRequestId
  const selectedRange = getStatsRange(statsOffset.value)
  const from = toIsoDate(selectedRange.start)
  const to = toIsoDate(selectedRange.end)
  const period = statRange.value === 'today' ? 'day' : statRange.value
  statsLoading.value = true
  statsError.value = null
  try {
    const [range, comparison, studentRanking, leaveRows] = await Promise.all([
      statsApi.range(from, to, selectedRange.granularity),
      statsApi.comparison(from, to, period),
      statsApi.students(from, to),
      statsApi.leave(from, to),
    ])
    if (requestId !== statsRequestId) return
    rangeStats.value = range
    comparisonStats.value = comparison
    ranking.value = studentRanking
    leaveItems.value = leaveRows
  } catch (error) {
    if (requestId === statsRequestId && !isCancel(error)) {
      statsError.value = loadError(error, '统计数据加载失败，请稍后重试')
    }
  } finally {
    if (requestId === statsRequestId) {
      statsLoading.value = false
    }
  }
}

async function loadStudentDetail() {
  const requestId = ++studentDetailRequestId
  if (!selectedStudentId.value) {
    selectedStudentDetail.value = null
    studentDetailError.value = null
    studentDetailLoading.value = false
    return
  }
  const studentId = selectedStudentId.value
  studentDetailLoading.value = true
  studentDetailError.value = null
  try {
    const detail = await studentsApi.get(studentId)
    if (requestId === studentDetailRequestId && selectedStudentId.value === studentId) {
      selectedStudentDetail.value = detail
    }
  } catch (error) {
    if (requestId === studentDetailRequestId && selectedStudentId.value === studentId && !isCancel(error)) {
      studentDetailError.value = loadError(error, '学生详情加载失败')
    }
  } finally {
    if (requestId === studentDetailRequestId && selectedStudentId.value === studentId) {
      studentDetailLoading.value = false
    }
  }
}

async function loadTemplates() {
  const requestId = ++templatesRequestId
  if (!selectedStudentId.value) {
    templates.value = []
    templatesError.value = null
    templatesLoading.value = false
    return
  }
  const studentId = selectedStudentId.value
  templatesLoading.value = true
  templatesError.value = null
  try {
    const rows = await templatesApi.list(studentId)
    if (requestId === templatesRequestId && selectedStudentId.value === studentId) {
      templates.value = rows
    }
  } catch (error) {
    if (requestId === templatesRequestId && selectedStudentId.value === studentId && !isCancel(error)) {
      templatesError.value = loadError(error, '模板加载失败')
    }
  } finally {
    if (requestId === templatesRequestId && selectedStudentId.value === studentId) {
      templatesLoading.value = false
    }
  }
}

async function loadStudentWorkspace() {
  await Promise.all([loadStudentDetail(), loadTemplates()])
}

async function refreshStudentWorkspace() {
  await loadDashboard()
  await loadStudentWorkspace()
}

async function downloadMonthReport() {
  statsError.value = null
  try {
    const range = getStatsRange(statsOffset.value)
    const blob = await exportApi.downloadXlsx(toIsoDate(range.start), toIsoDate(range.end))
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `kebiao_${toIsoDate(range.start)}_${toIsoDate(range.end)}.xlsx`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (error) {
    if (!isCancel(error)) statsError.value = loadError(error, '报表导出失败，请稍后重试')
  }
}

async function openStudentWorkspace(studentId: number) {
  selectedStudentId.value = studentId
  await router.push({ path: '/students', query: { student: String(studentId) } })
}

async function moveLesson(payload: { lesson: Lesson; date: string; start_time: string }) {
  scheduleError.value = ''
  pendingMovePayload.value = payload
  showRescheduleMode.value = true
}

async function handleRescheduleMode(mode: '1' | '2' | '3') {
  showRescheduleMode.value = false
  const payload = pendingMovePayload.value
  if (!payload) return

  if (mode === '3') {
    selectedStudentId.value = payload.lesson.student_id
    activeTab.value = 'students'
    scheduleError.value = '请在学生页编辑对应周课表模板'
    return
  }
  if (mode === '2') {
    scheduleError.value = '本次及以后需要批量重排后续实例；当前请通过模板编辑完成'
    return
  }
  try {
    await lessonsApi.update(payload.lesson.id, {
      date: payload.date,
      start_time: payload.start_time,
      duration_hours: payload.lesson.duration_hours,
      status: payload.lesson.status,
    })
    await loadDashboard()
  } catch {
    scheduleError.value = '移动失败：目标时间可能存在冲突'
  }
}

function toggleBulkLesson(lesson: Lesson) {
  if (bulkSelectedIds.value.includes(lesson.id)) {
    bulkSelectedIds.value = bulkSelectedIds.value.filter((id) => id !== lesson.id)
  } else {
    bulkSelectedIds.value = [...bulkSelectedIds.value, lesson.id]
  }
}

async function runBulkAction(action: 'complete' | 'cancel' | 'restore' | 'delete') {
  if (!bulkSelectedIds.value.length) return
  if (action === 'delete' || action === 'cancel') {
    pendingDangerAction.value = {
      kind: action === 'delete' ? 'bulk-delete' : 'bulk-cancel',
      lessonIds: [...bulkSelectedIds.value],
    }
    return
  }
  scheduleError.value = ''
  try {
    await lessonsApi.bulk({ ids: bulkSelectedIds.value, action })
    bulkSelectedIds.value = []
    await loadDashboard()
  } catch {
    scheduleError.value = '批量操作失败：请检查所选课时状态或时间冲突'
  }
}

function openCreateLesson() {
  showCreateLesson.value = true
}

function openLessonEdit(lesson: Lesson) {
  selectedLesson.value = lesson
}

function openStudentCreate() {
  studentFormMode.value = 'create'
  editingStudent.value = null
  showStudentForm.value = true
}

function openStudentEdit(studentId: number) {
  const student = students.value.find((s) => s.id === studentId) ?? null
  if (!student) return
  studentFormMode.value = 'edit'
  editingStudent.value = student
  showStudentForm.value = true
}

function openTemplateCreate() {
  templateFormMode.value = 'create'
  editingTemplate.value = null
  showTemplateForm.value = true
}

function openTemplateEdit(template: Template) {
  templateFormMode.value = 'edit'
  editingTemplate.value = template
  showTemplateForm.value = true
}

function handleOpenReschedule() {
  rescheduleTarget.value = selectedLesson.value
  showRescheduleLesson.value = true
}

async function handleQuickComplete(lesson: Lesson) {
  try {
    await lessonsApi.update(lesson.id, { status: '已完成' })
    mobileActionLesson.value = null
    await loadDashboard()
  } catch { scheduleError.value = '操作失败' }
}

async function handleQuickRestore(lesson: Lesson) {
  try {
    await lessonsApi.restore(lesson.id)
    mobileActionLesson.value = null
    await loadDashboard()
  } catch { scheduleError.value = '操作失败' }
}

function handleQuickCancel(lesson: Lesson) {
  pendingDangerAction.value = { kind: 'lesson-cancel', lesson }
}

function handleQuickReschedule(lesson: Lesson) {
  mobileActionLesson.value = null
  selectedLesson.value = lesson
  handleOpenReschedule()
}

function handleQuickDelete(lesson: Lesson) {
  pendingDangerAction.value = { kind: 'lesson-delete', lesson }
}

async function confirmDangerAction() {
  const action = pendingDangerAction.value
  if (!action || dangerSubmitting.value) return
  dangerSubmitting.value = true
  scheduleError.value = ''
  try {
    if (action.kind === 'lesson-delete') {
      await lessonsApi.remove(action.lesson.id)
      mobileActionLesson.value = null
    } else if (action.kind === 'lesson-cancel') {
      await lessonsApi.cancel(action.lesson.id)
      mobileActionLesson.value = null
    } else {
      await lessonsApi.bulk({ ids: action.lessonIds, action: action.kind === 'bulk-delete' ? 'delete' : 'cancel' })
      bulkSelectedIds.value = []
    }
    pendingDangerAction.value = null
    await loadDashboard()
  } catch {
    scheduleError.value = action.kind === 'lesson-delete' ? '删除失败，请稍后重试'
      : action.kind === 'lesson-cancel' ? '请假操作失败，请稍后重试'
        : action.kind === 'bulk-delete' ? '批量删除失败，请检查所选课时后重试'
          : '批量请假失败，请检查所选课时后重试'
  } finally {
    dangerSubmitting.value = false
  }
}

function handleMobileEdit(lesson: Lesson) {
  mobileActionLesson.value = null
  openLessonEdit(lesson)
}

async function handleUpdateNote(payload: { lessonId: number; note: string | null }) {
  try {
    await lessonsApi.update(payload.lessonId, { note: payload.note })
    await loadDashboard()
  } catch { scheduleError.value = '备注保存失败' }
}

watch(selectedStudentId, async () => {
  await loadStudentWorkspace()
})

watch(statRange, async () => {
  if (statsOffset.value !== 0) {
    statsOffset.value = 0
    return
  }
  await loadStatistics()
})

watch(statsOffset, async () => {
  await loadStatistics()
})

watch(weekOffset, async () => {
  if (viewMode.value === 'week') await loadDashboard()
})

watch(
  () => route.fullPath,
  async (_fullPath, previousFullPath) => {
    const nextTab = tabFromPath(route.path)
    activeTab.value = nextTab
    if (nextTab === 'students' && students.value.length) {
      const requestedStudentId = Number(route.query.student) || selectedStudentId.value
      selectedStudentId.value = normalizeSelectedStudentId(students.value, requestedStudentId)
    }
    if (nextTab === 'stats' && previousFullPath !== undefined) {
      await loadStatistics()
    }
  },
  { immediate: true }
)

watch(quickCreate, (value) => {
  if (value) {
    showCreateLesson.value = true
  }
})

onMounted(async () => {
  await settingsStore.refresh()
  await Promise.all([
    loadDashboard(),
    activeTab.value === 'stats' ? loadStatistics() : Promise.resolve(),
  ])
})
</script>

<template>
  <AppShell
    :active-tab="activeTab"
    :completed-count="comparisonStats?.current_lessons ?? 0"
    @change-tab="activeTab = $event"
  >
    <div v-if="loading" class="sticky top-0 z-20 h-0.5 w-full overflow-hidden rounded-full bg-[var(--accent)]/20">
      <div class="animate-load h-full w-1/3 rounded-full bg-[var(--accent)]" />
    </div>

    <section v-if="activeTab === 'schedule'" class="space-y-4">
      <ScheduleDashboardHeader
        :avatar-color="avatarColor"
        :display-name="displayName"
        :today-lessons="todayLessons"
        @create="openCreateLesson"
      />

      <div class="glass-strong sticky top-2 z-30 flex flex-wrap items-center justify-between gap-3 !rounded-2xl px-2.5 py-2">
        <div class="flex items-center gap-2">
          <button data-action="previous-period" class="btn-ghost btn-sm !px-2" @click="viewMode === 'day' ? handlePrevDay() : viewMode === 'month' ? handlePrevMonth() : prevWeek()">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
          </button>
          <button class="btn-ghost btn-sm !px-2" @click="goToToday">
            <span class="text-xs font-semibold">今天</span>
          </button>
          <button data-action="next-period" class="btn-ghost btn-sm !px-2" @click="viewMode === 'day' ? handleNextDay() : viewMode === 'month' ? handleNextMonth() : nextWeek()">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
          </button>
          <span v-if="viewMode === 'week'" class="text-xs font-semibold sm:text-sm">{{ weekRangeLabel }}</span>
        </div>
        <div class="flex items-center gap-1 sm:gap-1.5">
          <div class="flex items-center rounded-xl bg-white/40 p-0.5 dark:bg-white/8">
            <button
              v-for="m in (['month', 'week', 'day'] as const)"
              :key="m"
              :class="['rounded-lg px-2.5 py-1 text-xs font-medium transition-colors sm:px-3', viewMode === m ? 'bg-[var(--accent)] text-white shadow-sm' : 'text-[var(--text-dim)] hover:text-[var(--text)]']"
              @click="handleViewChange(m)"
            >
              {{ m === 'month' ? '月' : m === 'week' ? '周' : '日' }}
            </button>
          </div>
          <button class="btn-ghost btn-sm hidden !px-2.5 lg:inline-flex" @click="openCreateLesson">+</button>
          <button class="btn-primary btn-sm hidden sm:flex" @click="downloadMonthReport">导出 Excel</button>
        </div>
      </div>

      <ErrorNotice v-if="dashboardError" :error="dashboardError" @retry="loadDashboard" />

      <p v-if="scheduleError" class="rounded-2xl bg-red-500/10 px-4 py-2.5 text-sm text-red-600 dark:text-red-400">
        {{ scheduleError }}
      </p>

      <div
        v-if="bulkSelectedIds.length && viewMode === 'week'"
        class="glass flex flex-wrap items-center justify-between gap-3 p-3"
      >
        <span class="text-sm font-medium text-[var(--text)]">已选 {{ bulkSelectedIds.length }} 节</span>
        <div class="flex flex-wrap gap-1.5">
          <button class="btn-ghost btn-sm" @click="runBulkAction('complete')">批量完成</button>
          <button class="btn-ghost btn-sm" @click="runBulkAction('cancel')">批量请假</button>
          <button class="btn-ghost btn-sm" @click="runBulkAction('restore')">批量恢复</button>
          <button data-action="bulk-delete" class="btn-danger btn-sm" @click="runBulkAction('delete')">批量删除</button>
          <button class="btn-ghost btn-sm" @click="bulkSelectedIds = []">清空</button>
        </div>
      </div>

      <div :class="viewMode === 'week' ? 'xl:grid xl:grid-cols-[minmax(0,1fr)_230px] xl:items-start xl:gap-4' : ''">
        <div class="min-w-0">
          <MonthView
            v-if="viewMode === 'month'"
            :base-date="monthDate"
            :currency-symbol="currencySymbol"
            :refresh-key="refreshKey"
            :students="students"
            @day-click="handleDayClick"
            @select-lesson="openLessonEdit"
          />

          <DayView
            v-else-if="viewMode === 'day'"
            :currency-symbol="currencySymbol"
            :date-iso="selectedDay || toIsoDate(addDays(new Date(), weekOffset * 7))"
            :refresh-key="refreshKey"
            :students="students"
            :visible-end="settingsStore.settings.visible_time_end"
            :visible-start="settingsStore.settings.visible_time_start"
            @create-at="quickCreate = $event"
            @select-lesson="openLessonEdit"
          />

          <ScheduleBoard
            v-else
            :currency-symbol="currencySymbol"
            :lessons="lessons"
            :selected-lesson-ids="bulkSelectedIds"
            :selected-lesson-id="selectedLesson?.id ?? null"
            :visible-end="settingsStore.settings.visible_time_end"
            :visible-start="settingsStore.settings.visible_time_start"
            :week-start="currentWeekStart"
            @create-at="quickCreate = $event"
            @move-lesson="moveLesson"
            @select-lesson="openLessonEdit"
            @open-mobile-actions="mobileActionLesson = $event"
            @swipe-next="viewMode === 'week' ? nextWeek() : viewMode === 'month' ? handleNextMonth() : handleNextDay()"
            @swipe-prev="viewMode === 'week' ? prevWeek() : viewMode === 'month' ? handlePrevMonth() : handlePrevDay()"
            @complete-lesson="handleQuickComplete"
            @restore-lesson="handleQuickRestore"
            @cancel-lesson="handleQuickCancel"
            @reschedule-lesson="handleQuickReschedule"
            @delete-lesson="handleQuickDelete"
            @toggle-bulk="toggleBulkLesson"
            @update-note="handleUpdateNote"
          />
        </div>

        <ScheduleOverview
          v-if="viewMode === 'week'"
          :active-student-count="students.length"
          :today-lessons="todayLessons"
        />
      </div>

      <button
        class="fab-create fixed bottom-20 right-4 z-40 grid h-14 w-14 place-items-center rounded-[20px] text-2xl text-white shadow-[0_16px_32px_rgba(139,57,181,0.32)] lg:hidden"
        style="background: var(--accent-gradient)"
        aria-label="新建课程"
        @click="openCreateLesson"
      >
        +
      </button>

      <MobileLessonActionsSheet
        :currency-symbol="currencySymbol"
        :lesson="mobileActionLesson"
        @cancel="handleQuickCancel"
        @close="mobileActionLesson = null"
        @complete="handleQuickComplete"
        @delete="handleQuickDelete"
        @edit="handleMobileEdit"
        @reschedule="handleQuickReschedule"
        @restore="handleQuickRestore"
      />

      <CreateLessonModal
        v-if="showCreateLesson"
        :currency-symbol="currencySymbol"
        :default-duration="settingsStore.settings.default_duration_hours"
        :quick-create="quickCreate"
        :students="students"
        @close="showCreateLesson = false; quickCreate = null"
        @refresh="loadDashboard"
      />

      <LessonEditModal
        v-if="selectedLesson"
        :currency-symbol="currencySymbol"
        :default-duration="settingsStore.settings.default_duration_hours"
        :lesson="selectedLesson"
        :students="students"
        @close="selectedLesson = null"
        @open-reschedule="handleOpenReschedule"
        @refresh="loadDashboard"
      />

      <RescheduleLessonModal
        v-if="showRescheduleLesson && rescheduleTarget"
        :currency-symbol="currencySymbol"
        :default-duration="settingsStore.settings.default_duration_hours"
        :lesson="rescheduleTarget"
        @close="showRescheduleLesson = false; rescheduleTarget = null"
        @refresh="loadDashboard"
      />

      <RescheduleModeModal
        :visible="showRescheduleMode"
        @close="showRescheduleMode = false; pendingMovePayload = null"
        @select="handleRescheduleMode"
      />

      <ConfirmDialog
        :open="Boolean(pendingDangerAction)"
        :title="pendingDangerAction?.kind === 'bulk-delete' ? '批量删除课程？'
          : pendingDangerAction?.kind === 'bulk-cancel' ? '批量标记请假？'
            : pendingDangerAction?.kind === 'lesson-cancel' ? '将这节课程标记为请假？' : '删除这节课程？'"
        :description="pendingDangerAction?.kind === 'bulk-delete'
          ? `将永久删除所选 ${pendingDangerAction.lessonIds.length} 节课程，此操作不可撤销。`
          : pendingDangerAction?.kind === 'bulk-cancel'
            ? `将所选 ${pendingDangerAction.lessonIds.length} 节课程标记为请假，不计入已完成课时。`
            : pendingDangerAction?.kind === 'lesson-cancel'
              ? `将 ${pendingDangerAction.lesson.student?.name ?? '所选学生'} 的这节课程标记为请假，之后仍可恢复。`
              : `将永久删除 ${pendingDangerAction?.lesson.student?.name ?? '所选学生'} 的这节课程，此操作不可撤销。`"
        :confirm-label="pendingDangerAction?.kind === 'lesson-cancel' || pendingDangerAction?.kind === 'bulk-cancel' ? '确认请假' : '确认删除'"
        :tone="pendingDangerAction?.kind === 'lesson-cancel' || pendingDangerAction?.kind === 'bulk-cancel' ? 'primary' : 'danger'"
        :pending="dangerSubmitting"
        pending-label="删除中…"
        @update:open="!$event && (pendingDangerAction = null)"
        @confirm="confirmDangerAction"
      />
    </section>

    <section v-else-if="activeTab === 'students'" class="pb-4">
      <div class="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)] lg:items-start">
        <StudentsPanel
          :currency-symbol="currencySymbol"
          :selected-student-id="selectedStudentId"
          :students="students"
          @select-student="selectedStudentId = $event"
          @edit-student="openStudentEdit"
          @add-student="openStudentCreate"
        />
        <div class="min-w-0 space-y-4">
          <StudentOverview
            :currency-symbol="currencySymbol"
            :error="studentDetailError"
            :loading="studentDetailLoading"
            :student="selectedStudentDetail"
            @edit-student="openStudentEdit"
            @retry="loadStudentDetail"
          />
          <TemplateManager
            :error="templatesError"
            :loading="templatesLoading"
            :selected-student-id="selectedStudentId"
            :students="students"
            :templates="templates"
            @retry="loadTemplates"
            @edit-template="openTemplateEdit"
            @add-template="openTemplateCreate"
          />
        </div>
      </div>

      <StudentFormModal
        v-if="showStudentForm"
        :currency-symbol="currencySymbol"
        :mode="studentFormMode"
        :student="editingStudent"
        @close="showStudentForm = false"
        @refresh="refreshStudentWorkspace"
      />

      <TemplateFormModal
        v-if="showTemplateForm"
        :mode="templateFormMode"
        :selected-student-id="selectedStudentId"
        :students="students"
        :template="editingTemplate"
        @close="showTemplateForm = false"
        @refresh-templates="loadStudentWorkspace"
      />
    </section>

    <section v-else-if="activeTab === 'stats'">
      <StatsPanel
        :comparison="comparisonStats"
        :currency-symbol="currencySymbol"
        :is-current-period="isCurrentStatsPeriod"
        :leave-items="leaveItems"
        :range="rangeStats"
        :ranking="ranking"
        :stat-range="statRange"
        :stats-offset="statsOffset"
        :stats-period-label="statsPeriodLabel"
        :today="todayStats"
        :loading="statsLoading"
        :error="statsError"
        @change-range="statRange = $event"
        @export-range="downloadMonthReport"
        @go-current-period="goToCurrentStatsPeriod"
        @next-period="nextStatsPeriod"
        @prev-period="prevStatsPeriod"
        @retry="loadStatistics"
        @select-student="openStudentWorkspace"
      />
    </section>

    <section v-else>
      <SettingsPanel />
    </section>
  </AppShell>
</template>
