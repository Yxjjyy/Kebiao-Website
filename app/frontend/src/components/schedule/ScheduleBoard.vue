<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { Lesson } from '@/api/types'
import { formatHourMinute, formatShortDate, formatWeekday, getWeekDays, isToday, toIsoDate } from '@/lib/date'
import { formatCurrency, formatHours } from '@/lib/format'
import { useSettingsStore } from '@/stores/settings'
import { downloadICS } from '@/composables/useCalendar'

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
}>()

const draggingLessonId = ref<number | null>(null)
const dragOverSlotKey = ref<string | null>(null)
const dragOverConflict = ref(false)
const showUndo = ref(false)
const undoInfo = ref('')
const collapsedDays = ref<Set<string>>(new Set())
const editingNoteId = ref<number | null>(null)
const editingNoteValue = ref('')

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

function toggleDay(iso: string) {
  const next = new Set(collapsedDays.value)
  if (next.has(iso)) next.delete(iso); else next.add(iso)
  collapsedDays.value = next
}

const occupiedSlots = computed(() => {
  const set = new Set<string>()
  for (const lesson of props.lessons) set.add(`${lesson.date}-${lesson.start_time}`)
  return set
})

const weekdays = computed(() =>
  getWeekDays(props.weekStart, (settingsStore.settings.week_start as 0 | 1) ?? 1).map((day) => ({
    iso: toIsoDate(day),
    label: formatWeekday(day),
    sublabel: formatShortDate(day),
    today: isToday(toIsoDate(day)),
  }))
)

watch(
  () => weekdays.value.map((d) => d.iso),
  (isos) => {
    const todayIso = toIsoDate(new Date())
    collapsedDays.value = new Set(isos.filter((iso) => iso < todayIso))
  },
  { immediate: true }
)

const grouped = computed(() =>
  weekdays.value.map((day) => ({ ...day, lessons: props.lessons.filter((l) => l.date === day.iso).sort((a, b) => a.start_time.localeCompare(b.start_time)) }))
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
  const now = new Date()
  const v = now.getHours() + now.getMinutes() / 60
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
  dragOverConflict.value = occupiedSlots.value.has(`${dayIso}-${slot}`) && !(dl.date === dayIso && dl.start_time === slot)
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

    <!-- Mobile -->
    <div class="grid gap-2.5 lg:hidden">
      <article v-for="day in grouped" :key="day.iso" class="glass rounded-2xl p-3">
        <div class="flex cursor-pointer items-center justify-between" @click="toggleDay(day.iso)">
          <div class="flex items-center gap-2">
            <svg class="h-4 w-4 text-[var(--text-dim)] transition-transform duration-200" :class="collapsedDays.has(day.iso) ? '' : 'rotate-90'" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            <p class="text-sm font-semibold">{{ day.label }} {{ day.sublabel }}</p>
            <span class="h-2 w-2 rounded-full" :class="day.today ? 'bg-[var(--accent)] shadow-[0_0_0_5px_rgba(76,125,255,0.18)]' : 'bg-white/50 dark:bg-white/20'" />
          </div>
          <div class="flex items-center gap-2">
            <span v-if="day.lessons.length" class="text-[11px] text-[var(--text-dim)]">{{ day.lessons.length }}节</span>
            <span v-if="day.today" class="text-[10px] text-[var(--accent)] font-medium">今天</span>
          </div>
        </div>

        <div v-if="!collapsedDays.has(day.iso)" class="mt-3 space-y-2">
          <div v-for="lesson in day.lessons" :key="lesson.id" :class="['cursor-pointer rounded-xl border px-3 py-3 transition-all min-h-[56px]', lesson.id === selectedLessonId ? 'border-[var(--accent)] ring-2 ring-[var(--accent)]/20' : 'border-white/40 dark:border-white/10 active:bg-white/40']" :style="lessonBg(lesson)" @click="emit('select-lesson', lesson)">
            <div class="flex items-center justify-between gap-2">
              <div class="min-w-0">
                <p class="truncate text-sm font-semibold">{{ lesson.student?.name ?? `学生 #${lesson.student_id}` }}</p>
                <p class="mt-0.5 text-xs text-[var(--text-dim)]">{{ formatHourMinute(lesson.start_time) }} · {{ formatHours(lesson.duration_hours) }}</p>
              </div>
              <span :class="['badge text-[11px]', statusClass(lesson.status)]">{{ lesson.status }}</span>
            </div>
            <div class="mt-2.5 flex items-center justify-between text-xs text-[var(--text-dim)]">
              <span class="font-medium">{{ formatCurrency(lesson.price, currencySymbol) }}</span>
              <span v-if="editingNoteId === lesson.id" class="ml-2 flex-1" @click.stop>
                <input :data-note-input="lesson.id" v-model="editingNoteValue" class="w-full bg-transparent border-b border-dashed border-[var(--accent)] outline-none text-xs text-right" @keydown.enter.stop="saveNote(lesson.id)" @keydown.escape.stop="cancelEditNote()" @blur="saveNote(lesson.id)" />
              </span>
              <span v-else class="truncate ml-2 cursor-pointer hover:text-[var(--accent)]" @click.stop="startEditNote(lesson)">{{ lesson.note || '添加备注' }}</span>
            </div>
            <!-- Mobile action buttons -->
            <div class="mt-2.5 flex flex-wrap gap-1.5 border-t border-white/20 pt-2.5 dark:border-white/6" @click.stop>
              <button v-if="lesson.status === '待上'" class="btn-ghost btn-sm !py-1 !px-2 !text-[11px]" @click="emit('complete-lesson', lesson)">完成</button>
              <button v-if="lesson.status !== '待上'" class="btn-ghost btn-sm !py-1 !px-2 !text-[11px]" @click="emit('restore-lesson', lesson)">恢复待上</button>
              <button v-if="lesson.status === '待上'" class="btn-ghost btn-sm !py-1 !px-2 !text-[11px]" @click="emit('cancel-lesson', lesson)">请假</button>
              <button v-if="lesson.status === '待上'" class="btn-ghost btn-sm !py-1 !px-2 !text-[11px]" @click="emit('reschedule-lesson', lesson)">调课</button>
              <button class="btn-ghost btn-sm !py-1 !px-2 !text-[11px]" @click="downloadICS(lesson, lesson.student?.name ?? '课程')">📅</button>
              <button class="btn-danger btn-sm !py-1 !px-2 !text-[11px]" @click="emit('delete-lesson', lesson)">删除</button>
            </div>
          </div>
          <div v-if="!day.lessons.length" class="rounded-xl border border-dashed border-white/30 px-3 py-5 text-center text-xs text-[var(--text-dim)] dark:border-white/8">暂无课程</div>
        </div>
      </article>
    </div>

    <div v-if="showUndo" class="glass fixed bottom-20 left-1/2 z-50 -translate-x-1/2 rounded-2xl px-4 py-2.5 text-sm shadow-lg lg:bottom-6">
      <span class="text-[var(--text)]">已移动 {{ undoInfo }}</span>
    </div>
  </section>
</template>
