<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { Lesson } from '@/api/types'
import { lessonsApi } from '@/api/lessons'
import { formatHourMinute, formatShortDate, formatWeekday, isToday } from '@/lib/date'
import { formatCurrency, formatHours } from '@/lib/format'
import { useToast } from '@/composables/useToast'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()
const toast = useToast()

const props = defineProps<{
  currencySymbol: string
  dateIso: string
  visibleStart: string
  visibleEnd: string
  refreshKey: number
  students: { id: number; name: string; color: string }[]
}>()

const emit = defineEmits<{
  (e: 'select-lesson', lesson: Lesson): void
  (e: 'create-at', payload: { date: string; start_time: string }): void
}>()

const lessons = ref<Lesson[]>([])
const loading = ref(false)
const editingNoteId = ref<number | null>(null)
const editingNoteValue = ref('')
const loadError = ref('')
let dayRequestId = 0

function startEditNote(lesson: Lesson) {
  editingNoteId.value = lesson.id
  editingNoteValue.value = lesson.note ?? ''
  nextTick(() => {
    const input = document.querySelector(`[data-day-note-input="${lesson.id}"]`) as HTMLInputElement
    if (input) { input.focus(); input.select() }
  })
}

async function saveNote(lessonId: number) {
  if (editingNoteId.value === null) return
  const note = editingNoteValue.value || null
  const idx = lessons.value.findIndex((l) => l.id === lessonId)
  const previousNote = idx !== -1 ? lessons.value[idx].note : null
  if (idx !== -1) lessons.value[idx] = { ...lessons.value[idx], note }
  editingNoteId.value = null
  editingNoteValue.value = ''
  try {
    await lessonsApi.update(lessonId, { note })
  } catch {
    // 保存失败回滚本地乐观更新，避免界面显示未生效的假数据
    if (idx !== -1) lessons.value[idx] = { ...lessons.value[idx], note: previousNote }
    toast.show('备注保存失败')
  }
}

function cancelEditNote() {
  editingNoteId.value = null
  editingNoteValue.value = ''
}

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

const sortedLessons = computed(() =>
  [...lessons.value].sort((a, b) => a.start_time.localeCompare(b.start_time))
)

function lessonStyle(lesson: Lesson) {
  const [hour, minute] = lesson.start_time.split(':').map(Number)
  const offsetMin = (hour - startHour.value) * 60 + minute
  const top = (offsetMin / totalMinutes.value) * 100
  const height = (lesson.duration_hours * 60 / totalMinutes.value) * 100
  return {
    top: `${Math.max(0, top)}%`,
    height: `${Math.max(3, height)}%`,
  }
}

function lessonBg(color: string) {
  return { background: `linear-gradient(135deg, ${color}22, ${color}18)` }
}

const dateLabel = computed(() => formatWeekday(props.dateIso) + ' ' + formatShortDate(props.dateIso))
const todayClass = computed(() => isToday(props.dateIso, settingsStore.settings.timezone))

const nowLineTop = computed(() => {
  if (!todayClass.value) return null
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: settingsStore.settings.timezone,
    hour: 'numeric',
    minute: 'numeric',
    hourCycle: 'h23',
  }).formatToParts(new Date())
  const valueMap = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  const value = Number(valueMap.hour) + Number(valueMap.minute) / 60
  if (value < startHour.value || value > endHour.value + 1) return null
  return ((value - startHour.value) / Math.max(1, endHour.value - startHour.value + 1)) * 100
})

async function fetchDay() {
  const requestId = ++dayRequestId
  loading.value = true
  loadError.value = ''
  try {
    const rows = await lessonsApi.list(props.dateIso, props.dateIso)
    if (requestId !== dayRequestId) return
    lessons.value = rows
  } catch {
    if (requestId === dayRequestId) {
      loadError.value = '课程加载失败，请稍后重试'
      lessons.value = []
    }
  } finally {
    if (requestId === dayRequestId) loading.value = false
  }
}

watch(() => props.dateIso, () => { fetchDay() }, { immediate: true })
watch(() => props.refreshKey, () => { fetchDay() })
</script>

<template>
  <section class="glass p-4 md:p-5">
    <p v-if="loadError" class="mb-3 rounded-xl bg-red-500/10 px-3 py-2 text-center text-xs text-red-500">
      {{ loadError }}
    </p>
    <h3
      :class="[
        'mb-3 text-center text-sm font-semibold',
        todayClass ? 'text-[var(--accent)]' : '',
      ]"
    >
      {{ dateLabel }} {{ todayClass ? '(今天)' : '' }}
    </h3>

    <div class="relative" :style="{ height: `${timeSlots.length * 36}px` }">
      <div class="absolute left-16 right-0 top-0 bottom-0">
        <div
          v-for="slot in timeSlots"
          :key="slot"
          class="absolute left-0 right-0 border-t"
          :class="slot.endsWith(':30') ? 'border-dashed border-white/30 dark:border-white/6' : 'border-white/40 dark:border-white/8'"
          :style="{
            top: `${(timeSlots.indexOf(slot) / Math.max(1, timeSlots.length - 1)) * 100}%`,
            height: `${100 / Math.max(1, timeSlots.length - 1)}%`
          }"
          @click="emit('create-at', { date: dateIso, start_time: slot })"
        />

        <div
          v-if="nowLineTop !== null"
          class="absolute left-0 right-0 z-20 h-0.5 rounded-full bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.5)]"
          :style="{ top: `${nowLineTop}%` }"
        />

        <div
          v-for="lesson in sortedLessons"
          :key="lesson.id"
          :class="[
            'absolute left-1.5 right-1.5 z-10 cursor-pointer rounded-xl border border-white/50 px-3 py-2 text-left transition-all duration-150 hover:shadow-md dark:border-white/15',
          ]"
          :style="{ ...lessonStyle(lesson), ...lessonBg((students.find(s => s.id === lesson.student_id) || { color: '#4C7DFF' }).color) }"
          @click.stop="emit('select-lesson', lesson)"
        >
          <div class="flex items-center justify-between gap-2">
            <span class="text-sm font-semibold truncate">
              {{ (students.find(s => s.id === lesson.student_id) || { name: `#${lesson.student_id}` }).name }}
            </span>
            <span
              :class="[
                'badge text-[10px]',
                lesson.status === '已完成' ? 'badge-success' : lesson.status === '请假' ? 'badge-warning' : lesson.status === '已调课' ? 'badge-muted' : 'badge-info'
              ]"
            >
              {{ lesson.status }}
            </span>
          </div>
          <p class="mt-0.5 text-[11px] text-[var(--text-dim)]">
            {{ formatHourMinute(lesson.start_time) }} · {{ formatHours(lesson.duration_hours) }}
          </p>
          <p v-if="lesson.note || editingNoteId === lesson.id" class="mt-px text-[10px] text-[var(--text-dim)]" @click.stop="startEditNote(lesson)">
            <template v-if="editingNoteId === lesson.id">
              <input :data-day-note-input="lesson.id" v-model="editingNoteValue" class="w-full bg-transparent border-b border-dashed border-[var(--accent)] outline-none text-[10px]" @keydown.enter.stop="saveNote(lesson.id)" @keydown.escape.stop="cancelEditNote()" @blur="saveNote(lesson.id)" />
            </template>
            <template v-else>
              <span class="truncate block opacity-70">{{ lesson.note }}</span>
            </template>
          </p>
        </div>
      </div>

      <div class="absolute left-0 right-16 top-0 bottom-0">
        <div
          v-for="slot in timeSlots"
          :key="slot"
          class="absolute right-2 -translate-y-1/2 text-right text-[10px] text-[var(--text-dim)]"
          :class="slot.endsWith(':30') ? 'opacity-40' : 'font-medium opacity-70'"
          :style="{ top: `${(timeSlots.indexOf(slot) / Math.max(1, timeSlots.length - 1)) * 100}%` }"
        >
          {{ slot }}
        </div>
      </div>
    </div>
  </section>
</template>
