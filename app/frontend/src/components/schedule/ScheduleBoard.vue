<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { Lesson } from '@/api/types'
import { formatHourMinute, formatShortDate, formatWeekday, getWeekDays, getBusinessTodayIso, isToday, toIsoDate } from '@/lib/date'
import { formatCurrency, formatHours } from '@/lib/format'
import { resolveSelectedDate } from '@/lib/scheduleDashboard'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const props = defineProps<{
  lessons: Lesson[]
  currencySymbol: string
  selectedLessonId: number | null
  selectedLessonIds: number[]
  visibleStart: string
  visibleEnd: string
  weekStart: Date
}>()

const emit = defineEmits<{
  (e: 'select-lesson', lesson: Lesson): void
  (e: 'toggle-bulk', lesson: Lesson): void
  (e: 'create-at', payload: { date: string; start_time: string }): void
  (e: 'move-lesson', payload: { lesson: Lesson; date: string; start_time: string }): void
  (e: 'swipe-prev'): void
  (e: 'swipe-next'): void
  (e: 'complete-lesson', lesson: Lesson): void
  (e: 'restore-lesson', lesson: Lesson): void
  (e: 'cancel-lesson', lesson: Lesson): void
  (e: 'reschedule-lesson', lesson: Lesson): void
  (e: 'delete-lesson', lesson: Lesson): void
  (e: 'update-note', payload: { lessonId: number; note: string | null }): void
  (e: 'open-mobile-actions', lesson: Lesson): void
}>()

const draggingLessonId = ref<number | null>(null)
const dragOverSlotKey = ref<string | null>(null)
const dragOverConflict = ref(false)
const showUndo = ref(false)
const undoInfo = ref('')
const editingNoteId = ref<number | null>(null)
const editingNoteValue = ref('')
const selectedMobileDate = ref('')

function startEditNote(lesson: Lesson) {
  editingNoteId.value = lesson.id
  editingNoteValue.value = lesson.note ?? ''
  nextTick(() => {
    const input = document.querySelector(`[data-note-input="${lesson.id}"]`) as HTMLInputElement
    if (input) { input.focus(); input.select() }
  })
}

function saveNote(lessonId: number) {
  if (editingNoteId.value === null) return
  emit('update-note', { lessonId, note: editingNoteValue.value || null })
  editingNoteId.value = null
  editingNoteValue.value = ''
}

function cancelEditNote() {
  editingNoteId.value = null
  editingNoteValue.value = ''
}

// 与后端 find_conflicts 对齐：仅 待上/已完成 且时段重叠才算冲突
function activeWindows() {
  const map: Record<string, { id: number; start: number; end: number }[]> = {}
  for (const lesson of props.lessons) {
    if (lesson.status !== '待上' && lesson.status !== '已完成') continue
    const [hour, minute] = lesson.start_time.split(':').map(Number)
    const start = hour * 60 + minute
    const list = (map[lesson.date] ??= [])
    list.push({ id: lesson.id, start, end: start + Math.round(lesson.duration_hours * 60) })
  }
  return map
}

const weekdays = computed(() =>
  getWeekDays(props.weekStart, (settingsStore.settings.week_start as 0 | 1) ?? 1).map((day) => ({
    iso: toIsoDate(day),
    label: formatWeekday(day),
    sublabel: formatShortDate(day),
    today: isToday(toIsoDate(day), settingsStore.settings.timezone),
  }))
)

watch(
  () => weekdays.value.map((d) => d.iso),
  (isos) => {
    selectedMobileDate.value = resolveSelectedDate(isos, getBusinessTodayIso(settingsStore.settings.timezone))
  },
  { immediate: true }
)

const grouped = computed(() =>
  weekdays.value.map((day) => ({ ...day, lessons: props.lessons.filter((l) => l.date === day.iso).sort((a, b) => a.start_time.localeCompare(b.start_time)) }))
)
const selectedMobileDay = computed(() =>
  grouped.value.find((day) => day.iso === selectedMobileDate.value) ?? grouped.value[0]
)
const mobileCompletedCount = computed(() =>
  selectedMobileDay.value?.lessons.filter((lesson) => lesson.status === '已完成').length ?? 0
)

const startHour = computed(() => Number(props.visibleStart.slice(0, 2)))
const endHour = computed(() => Number(props.visibleEnd.slice(0, 2)))
const totalMinutes = computed(() => Math.max(1, (endHour.value - startHour.value) * 60))
const timeSlots = computed(() => {
  const rows: string[] = []
  for (let hour = startHour.value; hour <= endHour.value; hour++) {
    rows.push(`${String(hour).padStart(2, '0')}:00`)
    if (hour < endHour.value) rows.push(`${String(hour).padStart(2, '0')}:30`)
  }
  return rows
})

function lessonStyle(lesson: Lesson) {
  const [hour, minute] = lesson.start_time.split(':').map(Number)
  return { top: `${Math.max(0, ((hour - startHour.value) * 60 + minute) / totalMinutes.value * 100)}%`, height: `${Math.max(3, lesson.duration_hours * 60 / totalMinutes.value * 100)}%` }
}

function lessonBg(lesson: Lesson) {
  const color = lesson.student?.color ?? '#4C7DFF'
  return { background: `linear-gradient(135deg, ${color}22, ${color}18)` }
}

function statusClass(status: Lesson['status']) {
  switch (status) {
    case '已完成': return 'badge-success'
    case '请假':   return 'badge-warning'
    case '已调课': return 'badge-muted'
    default:       return 'badge-info'
  }
}

const nowLineTop = computed(() => {
  // 仅当视图包含业务时区的"今天"时显示当前时间线
  if (!weekdays.value.some((day) => day.today)) return null
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: settingsStore.settings.timezone,
    hour: 'numeric',
    minute: 'numeric',
    hourCycle: 'h23',
  }).formatToParts(new Date())
  const valueMap = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  const v = Number(valueMap.hour) + Number(valueMap.minute) / 60
  if (v < startHour.value || v > endHour.value + 1) return null
  return ((v - startHour.value) / Math.max(1, endHour.value - startHour.value + 1)) * 100
})

function onDragStart(event: DragEvent, lesson: Lesson) {
  draggingLessonId.value = lesson.id
  event.dataTransfer?.setData('text/plain', String(lesson.id))
  ;(event.currentTarget as HTMLElement).classList.add('opacity-40', 'scale-95')
  event.dataTransfer!.effectAllowed = 'move'
}

function onDragEnd(event: DragEvent) {
  ;(event.currentTarget as HTMLElement).classList.remove('opacity-40', 'scale-95')
  draggingLessonId.value = null
  dragOverSlotKey.value = null
}

function onDragOver(event: DragEvent, dayIso: string, slot: string) {
  event.preventDefault()
  dragOverSlotKey.value = `${dayIso}-${slot}`
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
  const lid = Number(event.dataTransfer?.getData('text/plain'))
  const dl = props.lessons.find((l) => l.id === lid)
  if (!dl) { dragOverConflict.value = false; return }
  const [hour, minute] = slot.split(':').map(Number)
  const start = hour * 60 + minute
  const end = start + Math.round(dl.duration_hours * 60)
  const windows = activeWindows()[dayIso] ?? []
  dragOverConflict.value = windows.some(
    (w) => w.id !== lid && start < w.end && w.start < end
  )
  const container = (event.currentTarget as HTMLElement).closest('.schedule-scroll') as HTMLElement
  if (container) {
    const rect = container.getBoundingClientRect()
    if (event.clientY - rect.top < 50) container.scrollTop -= 8
    else if (rect.bottom - event.clientY < 50) container.scrollTop += 8
  }
}

function onDragLeave() { dragOverSlotKey.value = null; dragOverConflict.value = false }

function onDrop(event: DragEvent, date: string, startTime: string) {
  const lid = Number(event.dataTransfer?.getData('text/plain'))
  const lesson = props.lessons.find((i) => i.id === lid)
  draggingLessonId.value = null; dragOverSlotKey.value = null
  if (!lesson) return
  undoInfo.value = `${lesson.student?.name ?? '课程'} → ${formatShortDate(date)} ${startTime.slice(0,5)}`
  showUndo.value = true
  setTimeout(() => { showUndo.value = false }, 4000)
  emit('move-lesson', { lesson, date, start_time: startTime })
}

let swipeStartX = 0, swipeStartY = 0
let lessonTouchStartX = 0, lessonTouchStartY = 0
let longPressTimer: ReturnType<typeof setTimeout> | null = null
let lessonTouchActive = false
const touchDragLesson = ref<Lesson | null>(null)

function onLessonTouchStart(e: TouchEvent, lesson: Lesson) {
  lessonTouchActive = true
  lessonTouchStartX = e.touches[0].clientX; lessonTouchStartY = e.touches[0].clientY
  longPressTimer = setTimeout(() => { touchDragLesson.value = lesson; draggingLessonId.value = lesson.id }, 400)
}

function onLessonTouchEnd(e: TouchEvent) {
  if (longPressTimer) { clearTimeout(longPressTimer); longPressTimer = null }
  if (!touchDragLesson.value) { lessonTouchActive = false; return }
  const t = e.changedTouches[0]
  if (Math.abs(t.clientX - lessonTouchStartX) < 10 && Math.abs(t.clientY - lessonTouchStartY) < 10) emit('select-lesson', touchDragLesson.value)
  touchDragLesson.value = null; draggingLessonId.value = null
  lessonTouchActive = false
}

function onSwipeStart(e: TouchEvent) {
  if (lessonTouchActive) return
  swipeStartX = e.touches[0].clientX; swipeStartY = e.touches[0].clientY
}
function onSwipeEnd(e: TouchEvent) {
  if (lessonTouchActive) return
  const dx = e.changedTouches[0].clientX - swipeStartX, dy = e.changedTouches[0].clientY - swipeStartY
  if (Math.abs(dx) < 80 || Math.abs(dx) < Math.abs(dy)) return
  if (dx > 0) emit('swipe-prev'); else emit('swipe-next')
}

function slotHeight() { return timeSlots.value.length * 28 }
function isEvenHour(slot: string) { return slot.endsWith(':00') && Number(slot.slice(0, 2)) % 2 === 0 }
</script>

<template>
  <section class="glass p-4 md:p-5 schedule-scroll" @touchstart="onSwipeStart" @touchend="onSwipeEnd">
    <div class="hidden gap-2.5 lg:grid lg:grid-cols-[56px_repeat(7,minmax(0,1fr))]">
      <div />
      <div v-for="day in grouped" :key="`${day.iso}-head`" :class="['rounded-2xl px-3 py-2.5 text-center text-xs font-semibold', day.today ? 'bg-[var(--accent)] text-white shadow-md' : 'bg-white/50 text-[var(--text-dim)] dark:bg-white/8']">{{ day.label }} {{ day.sublabel }}</div>

      <div class="relative" :style="{ height: `${slotHeight()}px` }">
        <div v-for="slot in timeSlots" :key="slot" :class="['absolute right-2 -translate-y-1/2 text-right text-[10px] text-[var(--text-dim)]', slot.endsWith(':30') ? 'opacity-40' : 'font-medium opacity-70']" :style="{ top: `${(timeSlots.indexOf(slot) / Math.max(1, timeSlots.length - 1)) * 100}%` }">{{ slot }}</div>
      </div>

      <article v-for="day in grouped" :key="`${day.iso}-grid`" :class="['relative overflow-hidden rounded-2xl border border-white/40 bg-white/30 dark:border-white/8 dark:bg-white/4', day.today ? 'border-l-[var(--accent)] border-l-2' : '']" :style="{ height: `${slotHeight()}px` }">
        <div v-for="slot in timeSlots" :key="`${day.iso}-${slot}`" :class="['absolute left-0 right-0 text-left transition-colors duration-150', slot.endsWith(':30') ? 'border-t border-dashed border-white/20 dark:border-white/[0.04]' : 'border-t border-white/35 dark:border-white/8', isEvenHour(slot) ? 'bg-white/[0.02] dark:bg-white/[0.01]' : '', dragOverSlotKey === `${day.iso}-${slot}` ? (dragOverConflict ? '!bg-red-500/15 !border-red-400/40 z-30' : '!bg-[var(--accent)]/15 !border-[var(--accent)]/40 z-30') : '']" :style="{ top: `${(timeSlots.indexOf(slot) / Math.max(1, timeSlots.length - 1)) * 100}%`, height: `${100 / Math.max(1, timeSlots.length - 1)}%` }" @dragover.prevent="onDragOver($event, day.iso, slot)" @dragleave="onDragLeave" @drop.prevent="onDrop($event, day.iso, slot)" @click="emit('create-at', { date: day.iso, start_time: slot })" />

        <div v-if="dragOverSlotKey && dragOverSlotKey.startsWith(day.iso) && !dragOverConflict" class="absolute left-1.5 right-1.5 z-25 pointer-events-none rounded-xl border-2 border-dashed border-[var(--accent)] bg-[var(--accent)]/5" :style="{ top: `${(timeSlots.indexOf(dragOverSlotKey.split('-').slice(1).join('-')) / Math.max(1, timeSlots.length - 1)) * 100}%`, height: `${100 / Math.max(1, timeSlots.length - 1)}%` }" />

        <div v-for="lesson in day.lessons" :key="lesson.id" draggable="true" :class="['group absolute left-1.5 right-1.5 z-10 cursor-pointer rounded-xl border border-white/50 px-2 py-1.5 text-left transition-all duration-150 dark:border-white/15', lesson.id === selectedLessonId ? 'ring-2 ring-[var(--accent)] ring-offset-1' : 'hover:shadow-md', lesson.id === draggingLessonId ? 'opacity-40 scale-95' : 'opacity-100']" :style="{ ...lessonStyle(lesson), ...lessonBg(lesson) }" @dragstart="onDragStart($event, lesson)" @dragend="onDragEnd" @click.stop="emit('select-lesson', lesson)" @touchstart.prevent="onLessonTouchStart($event, lesson)" @touchend="onLessonTouchEnd">
          <div class="flex items-center gap-1">
            <input class="h-3 w-3 rounded accent-[var(--accent)]" type="checkbox" :checked="selectedLessonIds.includes(lesson.id)" @click.stop @change.stop="emit('toggle-bulk', lesson)" />
            <span class="truncate text-[11px] font-semibold leading-tight">{{ lesson.student?.name ?? `#${lesson.student_id}` }}</span>
            <!-- Desktop hover action buttons -->
            <div class="ml-auto hidden items-center gap-0.5 group-hover:flex" @click.stop>
              <button v-if="lesson.status === '待上'" class="rounded-md px-1 py-0.5 text-[9px] font-medium text-emerald-600 hover:bg-emerald-500/15" title="完成" @click="emit('complete-lesson', lesson)">✓</button>
              <button v-if="lesson.status !== '待上'" class="rounded-md px-1 py-0.5 text-[9px] font-medium text-blue-600 hover:bg-blue-500/15" title="恢复待上" @click="emit('restore-lesson', lesson)">↩</button>
              <button v-if="lesson.status === '待上'" class="rounded-md px-1 py-0.5 text-[9px] font-medium text-amber-600 hover:bg-amber-500/15" title="请假" @click="emit('cancel-lesson', lesson)">✕</button>
              <button v-if="lesson.status === '待上'" class="rounded-md px-1 py-0.5 text-[9px] font-medium text-violet-600 hover:bg-violet-500/15" title="调课" @click="emit('reschedule-lesson', lesson)">↻</button>
              <button class="rounded-md px-1 py-0.5 text-[9px] font-medium text-red-500 hover:bg-red-500/15" title="删除" @click="emit('delete-lesson', lesson)">✕</button>
            </div>
          </div>
          <p class="mt-0.5 text-[10px] text-[var(--text-dim)]">{{ formatHourMinute(lesson.start_time) }} · {{ formatHours(lesson.duration_hours) }}</p>
          <p v-if="lesson.note || editingNoteId === lesson.id" class="mt-px text-[9px] text-[var(--text-dim)]" @click.stop="startEditNote(lesson)">
            <template v-if="editingNoteId === lesson.id">
              <input :data-note-input="lesson.id" v-model="editingNoteValue" class="w-full bg-transparent border-b border-dashed border-[var(--accent)] outline-none text-[9px]" @keydown.enter.stop="saveNote(lesson.id)" @keydown.escape.stop="cancelEditNote()" @blur="saveNote(lesson.id)" />
            </template>
            <template v-else>
              <span class="truncate block opacity-70">{{ lesson.note }}</span>
            </template>
          </p>
        </div>
      </article>
    </div>

    <!-- Mobile: single-day agenda -->
    <div class="lg:hidden">
      <div class="mb-3 flex items-end justify-between px-1">
        <div>
          <p class="text-sm font-bold">本周安排</p>
          <p class="mt-0.5 text-[11px] text-[var(--text-dim)]">{{ grouped[0]?.sublabel }} — {{ grouped[6]?.sublabel }}</p>
        </div>
        <p class="text-[11px] font-medium text-[var(--text-dim)]">
          {{ mobileCompletedCount }} / {{ selectedMobileDay?.lessons.length ?? 0 }} 已完成
        </p>
      </div>

      <div class="mb-4 grid grid-cols-7 gap-1.5" aria-label="选择日期">
        <button
          v-for="day in grouped"
          :key="day.iso"
          data-testid="mobile-date-option"
          :data-date="day.iso"
          :aria-pressed="selectedMobileDate === day.iso"
          :class="[
            'relative flex min-h-[58px] flex-col items-center justify-center rounded-2xl text-[11px] font-semibold transition-all duration-200',
            selectedMobileDate === day.iso
              ? 'text-white shadow-[0_9px_20px_rgba(141,62,188,0.22)]'
              : 'bg-white/55 text-[var(--text-dim)] dark:bg-white/[0.07]',
          ]"
          :style="selectedMobileDate === day.iso ? { background: 'var(--accent-gradient)' } : undefined"
          @click="selectedMobileDate = day.iso"
        >
          <span>{{ day.label.replace('星期', '') }}</span>
          <b class="mt-0.5 text-sm">{{ Number(day.iso.slice(-2)) }}</b>
          <i v-if="day.today && selectedMobileDate !== day.iso" class="absolute bottom-1 h-1 w-1 rounded-full bg-[var(--accent)]" />
        </button>
      </div>

      <div data-testid="mobile-course-list" class="space-y-2.5">
        <button
          v-for="lesson in selectedMobileDay?.lessons ?? []"
          :key="lesson.id"
          data-testid="mobile-course-card"
          class="mobile-course-card group w-full text-left"
          @click="emit('open-mobile-actions', lesson)"
        >
          <span class="w-12 shrink-0 text-sm font-bold tracking-tight">{{ formatHourMinute(lesson.start_time) }}</span>
          <span class="h-11 w-1 shrink-0 rounded-full" :style="{ background: `linear-gradient(180deg, ${lesson.student?.color ?? '#7c3aed'}, #ec4899)` }" />
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-bold">{{ lesson.student?.name ?? `学生 #${lesson.student_id}` }}</span>
            <span class="mt-1 block truncate text-[11px] text-[var(--text-dim)]">
              {{ formatHours(lesson.duration_hours) }} · {{ lesson.note || formatCurrency(lesson.price, currencySymbol) }}
            </span>
          </span>
          <span :class="['badge shrink-0 text-[10px]', statusClass(lesson.status)]">{{ lesson.status }}</span>
          <svg class="h-4 w-4 shrink-0 text-[#b8adbf] transition-transform group-active:translate-x-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="m9 18 6-6-6-6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>

        <div v-if="!selectedMobileDay?.lessons.length" class="glass flex min-h-32 flex-col items-center justify-center px-5 text-center">
          <span class="grid h-11 w-11 place-items-center rounded-2xl bg-[var(--accent-soft)] text-xl text-[var(--accent)]">◇</span>
          <p class="mt-3 text-sm font-semibold">今天没有课程</p>
          <p class="mt-1 text-xs text-[var(--text-dim)]">留一点时间给自己，或新建一节临时课。</p>
        </div>
      </div>
    </div>

    <div v-if="showUndo" class="glass fixed bottom-20 left-1/2 z-50 -translate-x-1/2 rounded-2xl px-4 py-2.5 text-sm shadow-lg lg:bottom-6">
      <span class="text-[var(--text)]">已移动 {{ undoInfo }}</span>
    </div>
  </section>
</template>
