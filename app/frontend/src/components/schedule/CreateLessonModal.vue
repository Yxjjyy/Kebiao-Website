<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { AxiosError } from 'axios'
import { lessonsApi } from '@/api/lessons'
import type { ConflictResponse, Student } from '@/api/types'
import { useToast } from '@/composables/useToast'
import { formatCurrency } from '@/lib/format'

const toast = useToast()

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => {
  document.body.style.overflow = 'hidden'
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.body.style.overflow = ''
  document.removeEventListener('keydown', onKeydown)
})

const props = defineProps<{
  students: Student[]
  defaultDuration: number
  currencySymbol: string
  quickCreate: { date: string; start_time: string } | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'refresh'): void
}>()

const form = reactive({
  student_id: 0,
  date: new Date().toISOString().slice(0, 10),
  start_time: '10:00',
  duration_hours: 1,
  note: '',
})

const error = ref('')
const submitting = ref(false)

watch(
  () => props.defaultDuration,
  (value) => {
    form.duration_hours = value
  },
  { immediate: true }
)

watch(
  () => props.quickCreate,
  (value) => {
    if (!value) return
    form.date = value.date
    form.start_time = value.start_time
  },
  { immediate: true }
)

const selectedStudentRate = computed(
  () => props.students.find((student) => student.id === form.student_id)?.hourly_rate ?? 0
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
  error.value = ''
  submitting.value = true
  try {
    await lessonsApi.create({
      student_id: form.student_id,
      date: form.date,
      start_time: form.start_time,
      duration_hours: form.duration_hours,
      note: form.note || null,
    })
    toast.show('课程已创建')
    emit('refresh')
    emit('close')
  } catch (err) {
    error.value = parseApiError(err)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="emit('close')">
      <div class="fixed inset-0 bg-black/30 modal-backdrop" />
      <div class="modal-panel glass-strong relative z-10 max-h-[85vh] w-full max-w-md overflow-y-auto p-6">
        <button class="absolute right-4 top-4 text-[var(--text-dim)] hover:text-[var(--text)]" @click="emit('close')">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>

        <h2 class="text-base font-semibold">新增临时课</h2>
        <p class="text-xs text-[var(--text-dim)]">一次性补课或临时新增</p>

        <form class="mt-4 space-y-3.5" @submit.prevent="createLesson">
          <label class="block">
            <span class="label">学生</span>
            <select v-model.number="form.student_id" class="input" required>
              <option disabled value="0">请选择学生</option>
              <option v-for="student in students" :key="student.id" :value="student.id">{{ student.name }}</option>
            </select>
          </label>
          <div class="grid gap-3.5 md:grid-cols-2">
            <label class="block">
              <span class="label">日期</span>
              <input v-model="form.date" class="input" type="date" required />
            </label>
            <label class="block">
              <span class="label">开始时间</span>
              <input v-model="form.start_time" class="input" type="time" required />
            </label>
          </div>
          <label class="block">
            <span class="label">课时</span>
            <select v-model.number="form.duration_hours" class="input">
              <option :value="0.5">0.5 小时</option>
              <option :value="1">1 小时</option>
              <option :value="1.5">1.5 小时</option>
            </select>
          </label>
          <label class="block">
            <span class="label">备注</span>
            <textarea v-model="form.note" class="input min-h-20 resize-y" />
          </label>
          <div class="rounded-xl bg-white/45 px-3 py-2 text-xs text-[var(--text-dim)] dark:bg-white/5">
            预估：{{ formatCurrency(selectedStudentRate * form.duration_hours, currencySymbol) }}
          </div>
          <button class="btn-primary w-full" :disabled="submitting">{{ submitting ? '创建中...' : '创建课时' }}</button>
        </form>

        <p v-if="error" class="mt-3 rounded-xl bg-red-500/10 px-3 py-2 text-xs text-red-600 dark:text-red-400">{{ error }}</p>
      </div>
    </div>
  </Teleport>
</template>
