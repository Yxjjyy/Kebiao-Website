<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { AxiosError } from 'axios'
import { lessonsApi } from '@/api/lessons'
import type { ConflictResponse, Lesson, Student } from '@/api/types'
import { formatCurrency } from '@/lib/format'
import { getBusinessTodayIso } from '@/lib/date'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

const props = defineProps<{
  lesson: Lesson | null
  students: Student[]
  defaultDuration: number
  currencySymbol: string
  quickCreate: { date: string; start_time: string } | null
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const createForm = reactive({
  student_id: 0,
  date: getBusinessTodayIso(settingsStore.settings.timezone),
  start_time: '10:00',
  duration_hours: 1,
  note: '',
})

const message = ref('')
const error = ref('')

watch(
  () => props.defaultDuration,
  (value) => {
    createForm.duration_hours = value
  },
  { immediate: true }
)

watch(
  () => props.quickCreate,
  (value) => {
    if (!value) return
    createForm.date = value.date
    createForm.start_time = value.start_time
  },
  { immediate: true }
)

const selectedStudentRate = computed(
  () => props.students.find((student) => student.id === createForm.student_id)?.hourly_rate ?? 0
)

function parseApiError(err: unknown) {
  if (err instanceof AxiosError) {
    const detail = err.response?.data as { detail?: ConflictResponse | string } | undefined
    if (detail && typeof detail.detail === 'object' && detail.detail.error === 'time_conflict') {
      return `时间冲突：${detail.detail.conflicts
        .map((item) => `${item.date} ${item.start_time} ${item.student_name}`)
        .join('；')}`
    }
    if (typeof detail?.detail === 'string') return detail.detail
  }
  return '操作失败，请稍后再试'
}

async function createLesson() {
  message.value = ''
  error.value = ''
  try {
    await lessonsApi.create({
      student_id: createForm.student_id,
      date: createForm.date,
      start_time: createForm.start_time,
      duration_hours: createForm.duration_hours,
      note: createForm.note || null,
    })
    message.value = '临时课已创建'
    emit('refresh')
  } catch (err) {
    error.value = parseApiError(err)
  }
}
</script>

<template>
  <section class="glass p-4 md:p-5">
    <h2 class="text-base font-semibold">新增临时课</h2>
    <p class="text-xs text-[var(--text-dim)]">一次性补课或临时新增</p>
    <form class="mt-4 space-y-3.5" @submit.prevent="createLesson">
      <label class="block">
        <span class="label">学生</span>
        <select v-model.number="createForm.student_id" class="input" required>
          <option disabled value="0">请选择学生</option>
          <option v-for="student in students" :key="student.id" :value="student.id">{{ student.name }}</option>
        </select>
      </label>
      <div class="grid gap-3.5 md:grid-cols-2">
        <label class="block">
          <span class="label">日期</span>
          <input v-model="createForm.date" class="input" type="date" required />
        </label>
        <label class="block">
          <span class="label">开始时间</span>
          <input v-model="createForm.start_time" class="input" type="time" required />
        </label>
      </div>
      <label class="block">
        <span class="label">课时</span>
        <select v-model.number="createForm.duration_hours" class="input">
          <option :value="0.5">0.5 小时</option>
          <option :value="1">1 小时</option>
          <option :value="1.5">1.5 小时</option>
        </select>
      </label>
      <label class="block">
        <span class="label">备注</span>
        <textarea v-model="createForm.note" class="input min-h-20 resize-y" />
      </label>
      <div class="rounded-xl bg-white/45 px-3 py-2 text-xs text-[var(--text-dim)] dark:bg-white/5">
        预估：{{ formatCurrency(selectedStudentRate * createForm.duration_hours, currencySymbol) }}
      </div>
      <button class="btn-primary w-full">创建课时</button>
    </form>
    <p v-if="message" class="mt-3 rounded-xl bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300">{{ message }}</p>
    <p v-if="error" class="mt-3 rounded-xl bg-red-500/10 px-3 py-2 text-xs text-red-600 dark:text-red-400">{{ error }}</p>
  </section>
</template>
