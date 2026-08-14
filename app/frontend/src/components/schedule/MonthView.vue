<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Lesson } from '@/api/types'
import { addDays, eachDayOfInterval, endOfMonth, format, startOfWeek, endOfWeek as endOfWeekFn, isSameDay, startOfMonth } from 'date-fns'
import { lessonsApi } from '@/api/lessons'
import { toIsoDate, isToday } from '@/lib/date'

const props = defineProps<{
  currencySymbol: string
  baseDate: Date
  refreshKey: number
  students: { id: number; name: string; color: string }[]
}>()

const emit = defineEmits<{
  (e: 'select-lesson', lesson: Lesson): void
  (e: 'day-click', date: string): void
}>()

const lessons = ref<Lesson[]>([])
const loading = ref(false)
const loadError = ref('')
let monthRequestId = 0

const monthStart = computed(() => startOfMonth(props.baseDate))
const gridStart = computed(() => startOfWeek(monthStart.value, { weekStartsOn: 1 }))
const gridEnd = computed(() => endOfWeekFn(endOfMonth(props.baseDate), { weekStartsOn: 1 }))

const days = computed(() => eachDayOfInterval({ start: gridStart.value, end: gridEnd.value }))

const weeks = computed(() => {
  const result: { iso: string; day: number; currentMonth: boolean; today: boolean }[][] = []
  for (let i = 0; i < days.value.length; i += 7) {
    result.push(days.value.slice(i, i + 7).map((d) => ({
      iso: toIsoDate(d),
      day: d.getDate(),
      currentMonth: d.getMonth() === props.baseDate.getMonth(),
      today: isToday(toIsoDate(d)),
    })))
  }
  return result
})

const lessonMap = computed(() => {
  const map: Record<string, Lesson[]> = {}
  for (const lesson of lessons.value) {
    const key = lesson.date
    if (!map[key]) map[key] = []
    map[key].push(lesson)
  }
  return map
})

function lessonBg(color: string) {
  return { background: `linear-gradient(135deg, ${color}33, ${color}1a)` }
}

function monthTitle() {
  return format(props.baseDate, 'yyyy年M月')
}

const weekdayHeaders = ['一', '二', '三', '四', '五', '六', '日']

async function fetchMonth() {
  const requestId = ++monthRequestId
  loading.value = true
  loadError.value = ''
  try {
    const from = toIsoDate(gridStart.value)
    const to = toIsoDate(gridEnd.value)
    const rows = await lessonsApi.list(from, to)
    if (requestId !== monthRequestId) return
    lessons.value = rows
  } catch {
    if (requestId === monthRequestId) {
      loadError.value = '课程加载失败，请稍后重试'
      lessons.value = []
    }
  } finally {
    if (requestId === monthRequestId) loading.value = false
  }
}

watch(() => props.baseDate.toISOString(), () => { fetchMonth() }, { immediate: true })
watch(() => props.refreshKey, () => { fetchMonth() })
</script>

<template>
  <section class="glass p-4 md:p-5">
    <p v-if="loadError" class="mb-3 rounded-xl bg-red-500/10 px-3 py-2 text-center text-xs text-red-500">
      {{ loadError }}
    </p>
    <h3 class="mb-3 text-center text-sm font-semibold">{{ monthTitle() }}</h3>

    <div class="grid grid-cols-7 gap-px rounded-xl bg-white/30 p-1 dark:bg-white/5">
      <div
        v-for="h in weekdayHeaders"
        :key="h"
        class="py-1.5 text-center text-[11px] font-semibold text-[var(--text-dim)]"
      >
        {{ h }}
      </div>

      <template v-for="week in weeks" :key="week[0].iso">
        <div
          v-for="day in week"
          :key="day.iso"
          :class="[
            'relative min-h-[52px] cursor-pointer p-1 transition-colors hover:bg-white/30 dark:hover:bg-white/5',
            day.today ? 'bg-[var(--accent)]/10 font-bold' : '',
            !day.currentMonth ? 'opacity-35' : '',
          ]"
          @click="emit('day-click', day.iso)"
        >
          <span
            :class="[
              'inline-flex h-5 w-5 items-center justify-center rounded-full text-[11px]',
              day.today ? 'bg-[var(--accent)] text-white' : '',
            ]"
          >
            {{ day.day }}
          </span>

          <div class="mt-0.5 space-y-0.5">
            <div
              v-for="lesson in (lessonMap[day.iso] || []).slice(0, 3)"
              :key="lesson.id"
              class="truncate rounded px-1 py-0.5 text-[9px] font-medium"
              :style="lessonBg((students.find(s => s.id === lesson.student_id) || { color: '#4C7DFF' }).color)"
              @click.stop="emit('select-lesson', lesson)"
            >
              {{ (students.find(s => s.id === lesson.student_id) || { name: `#${lesson.student_id}` }).name }} {{ lesson.start_time.slice(0,5) }}
            </div>
            <div
              v-if="(lessonMap[day.iso] || []).length > 3"
              class="text-[9px] text-[var(--text-dim)] pl-1"
            >
              +{{ (lessonMap[day.iso] || []).length - 3 }} 更多
            </div>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>
