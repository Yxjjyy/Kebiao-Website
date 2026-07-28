<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { AxiosError } from 'axios'
import { lessonsApi } from '@/api/lessons'
import type { ConflictResponse, Lesson, Student } from '@/api/types'
import { useToast } from '@/composables/useToast'
import { downloadICS } from '@/composables/useCalendar'
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
  lesson: Lesson | null
  students: Student[]
  defaultDuration: number
  currencySymbol: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'refresh'): void
  (e: 'open-reschedule'): void
}>()

const editForm = reactive({
  date: '',
  start_time: '',
  duration_hours: 1,
  status: '待上' as Lesson['status'],
  note: '',
})

const message = ref('')
const error = ref('')

watch(
  () => props.lesson,
  (lesson) => {
    if (!lesson) return
    editForm.date = lesson.date
    editForm.start_time = lesson.start_time
    editForm.duration_hours = lesson.duration_hours
    editForm.status = lesson.status
    editForm.note = lesson.note ?? ''
    message.value = ''
    error.value = ''
  },
  { immediate: true }
)

const studentName = computed(() => {
  if (!props.lesson) return ''
  return props.students.find((s) => s.id === props.lesson!.student_id)?.name ?? `学生 #${props.lesson!.student_id}`
})

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

async function updateStatus(status: Lesson['status']) {
  if (!props.lesson) return
  message.value = ''
  error.value = ''
  try {
    if (status === '请假') {
      await lessonsApi.cancel(props.lesson.id, editForm.note || undefined)
    } else if (status === '待上') {
      await lessonsApi.restore(props.lesson.id)
    } else {
      await lessonsApi.update(props.lesson.id, { status })
    }
    message.value = '课时已更新'
    toast.show('课时状态已更新')
    emit('refresh')
  } catch (err) {
    error.value = parseApiError(err)
  }
}

async function updateLesson() {
  if (!props.lesson) return
  message.value = ''
  error.value = ''
  try {
    await lessonsApi.update(props.lesson.id, {
      date: editForm.date,
      start_time: editForm.start_time,
      duration_hours: editForm.duration_hours,
      status: editForm.status,
      note: editForm.note || null,
    })
    message.value = '课时信息已保存'
    toast.show('课时已保存')
    emit('refresh')
  } catch (err) {
    error.value = parseApiError(err)
  }
}

async function removeLesson() {
  if (!props.lesson) return
  if (!window.confirm('确定删除该课时？此操作不可撤销')) return
  message.value = ''
  error.value = ''
  try {
    await lessonsApi.remove(props.lesson.id)
    toast.show('课时已删除')
    emit('refresh')
    emit('close')
  } catch (err) {
    error.value = parseApiError(err)
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4" @click.self="emit('close')">
      <div class="fixed inset-0 bg-black/30 modal-backdrop" />
      <div class="modal-panel glass-strong relative z-10 max-h-[85vh] w-full max-w-lg overflow-y-auto p-6">
        <button class="absolute right-4 top-4 text-[var(--text-dim)] hover:text-[var(--text)]" @click="emit('close')">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>

        <h2 class="text-base font-semibold">课时操作</h2>

        <div v-if="lesson" class="mt-4 space-y-4">
          <div class="rounded-2xl border border-white/35 bg-white/45 p-3.5 dark:border-white/8 dark:bg-white/5">
            <div class="flex items-center justify-between gap-3">
              <div>
                <p class="text-sm font-semibold">{{ studentName }}</p>
                <p class="text-xs text-[var(--text-dim)]">{{ lesson.date }} {{ lesson.start_time }} · {{ lesson.duration_hours }}h</p>
              </div>
              <span :class="['badge text-[11px]', lesson.status === '已完成' ? 'badge-success' : lesson.status === '请假' ? 'badge-warning' : lesson.status === '已调课' ? 'badge-muted' : 'badge-info']">{{ lesson.status }}</span>
            </div>
          </div>

          <div class="flex flex-wrap gap-1.5">
            <button class="btn-ghost btn-sm" @click="updateStatus('已完成')">完成</button>
            <button class="btn-ghost btn-sm" @click="updateStatus('请假')">请假</button>
            <button class="btn-ghost btn-sm" @click="updateStatus('待上')">恢复</button>
            <button v-if="lesson" class="btn-ghost btn-sm" @click="downloadICS(lesson, studentName)">📅 日历</button>
            <button class="btn-danger btn-sm" @click="removeLesson">删除</button>
          </div>

          <div class="border-t border-white/30 pt-4 dark:border-white/8">
            <h3 class="mb-3 text-sm font-semibold">编辑课时</h3>
            <form class="grid gap-3.5 md:grid-cols-2" @submit.prevent="updateLesson">
              <label class="block">
                <span class="label">日期</span>
                <input v-model="editForm.date" class="input" type="date" required />
              </label>
              <label class="block">
                <span class="label">时间</span>
                <input v-model="editForm.start_time" class="input" type="time" required />
              </label>
              <label class="block">
                <span class="label">课时</span>
                <select v-model.number="editForm.duration_hours" class="input">
                  <option :value="0.5">0.5h</option>
                  <option :value="1">1h</option>
                  <option :value="1.5">1.5h</option>
                </select>
              </label>
              <label class="block">
                <span class="label">状态</span>
                <select v-model="editForm.status" class="input">
                  <option value="待上">待上</option>
                  <option value="已完成">已完成</option>
                  <option value="请假">请假</option>
                  <option value="已调课">已调课</option>
                </select>
              </label>
              <label class="block md:col-span-2">
                <span class="label">备注</span>
                <textarea v-model="editForm.note" class="input min-h-16 resize-y" />
              </label>
              <div class="md:col-span-2 flex gap-2">
                <button class="btn-primary btn-sm">保存修改</button>
                <button type="button" class="btn-ghost btn-sm" @click="emit('open-reschedule')">调课 →</button>
              </div>
            </form>
          </div>
        </div>

        <div v-else class="mt-4 rounded-xl border border-dashed border-white/30 px-3 py-10 text-center text-xs text-[var(--text-dim)] dark:border-white/8">
          未选中课程
        </div>

        <p v-if="message" class="mt-3 rounded-xl bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300">{{ message }}</p>
        <p v-if="error" class="mt-3 rounded-xl bg-red-500/10 px-3 py-2 text-xs text-red-600 dark:text-red-400">{{ error }}</p>
      </div>
    </div>
  </Teleport>
</template>
