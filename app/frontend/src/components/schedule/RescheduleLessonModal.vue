<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { AxiosError } from 'axios'
import { lessonsApi } from '@/api/lessons'
import type { ConflictResponse, Lesson } from '@/api/types'
import { useToast } from '@/composables/useToast'

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
  lesson: Lesson | null
  defaultDuration: number
  currencySymbol: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'refresh'): void
}>()

const form = reactive({
  new_date: '',
  new_start_time: '',
  new_duration_hours: 1,
  note: '',
})

const message = ref('')
const error = ref('')
const submitting = ref(false)

watch(
  () => props.lesson,
  (lesson) => {
    if (!lesson) return
    form.new_date = lesson.date
    form.new_start_time = lesson.start_time
    form.new_duration_hours = lesson.duration_hours
    form.note = lesson.note ?? ''
    message.value = ''
    error.value = ''
  },
  { immediate: true }
)

function parseApiError(err: unknown) {
  if (err instanceof AxiosError) {
    const detail = err.response?.data as { detail?: ConflictResponse | string } | undefined
    if (detail && typeof detail.detail === 'object' && detail.detail.error === 'time_conflict') {
      return `时间冲突：${detail.detail.conflicts.map((item) => `${item.date} ${item.start_time} ${item.student_name}`).join('；')}`
    }
    if (typeof detail?.detail === 'string') return detail.detail
  }
  return '操作失败，请稍后再试'
}

async function submit() {
  if (!props.lesson) return
  message.value = ''
  error.value = ''
  submitting.value = true
  try {
    await lessonsApi.reschedule(props.lesson.id, {
      new_date: form.new_date,
      new_start_time: form.new_start_time,
      new_duration_hours: form.new_duration_hours,
      note: form.note || null,
    })
    toast.show('调课成功')
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

        <h2 class="text-base font-semibold">调课</h2>

        <div v-if="lesson" class="mt-4 space-y-4">
          <div class="rounded-2xl border border-white/35 bg-white/35 px-3 py-2.5 text-xs text-[var(--text-dim)] dark:border-white/8 dark:bg-white/5">
            原课：{{ lesson.date }} {{ lesson.start_time.slice(0,5) }} · {{ lesson.duration_hours }}h
          </div>

          <form class="grid gap-3.5 md:grid-cols-2" @submit.prevent="submit">
            <label class="block">
              <span class="label">新日期</span>
              <input v-model="form.new_date" class="input" type="date" required />
            </label>
            <label class="block">
              <span class="label">新时间</span>
              <input v-model="form.new_start_time" class="input" type="time" required />
            </label>
            <label class="block">
              <span class="label">新课時</span>
              <select v-model.number="form.new_duration_hours" class="input">
                <option :value="0.5">0.5h</option>
                <option :value="1">1h</option>
                <option :value="1.5">1.5h</option>
              </select>
            </label>
            <label class="block md:col-span-2">
              <span class="label">备注</span>
              <textarea v-model="form.note" class="input min-h-16 resize-y" />
            </label>
            <div class="md:col-span-2">
              <button class="btn-primary btn-sm" :disabled="submitting">{{ submitting ? '提交中...' : '确认调课' }}</button>
            </div>
          </form>
        </div>

        <p v-if="message" class="mt-3 rounded-xl bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300">{{ message }}</p>
        <p v-if="error" class="mt-3 rounded-xl bg-red-500/10 px-3 py-2 text-xs text-red-600 dark:text-red-400">{{ error }}</p>
      </div>
    </div>
  </Teleport>
</template>
