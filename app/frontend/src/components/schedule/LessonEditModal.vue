<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { lessonsApi } from '@/api/lessons'
import type { Lesson, Student } from '@/api/types'
import AppDialog from '@/components/ui/AppDialog.vue'
import AsyncButton from '@/components/ui/AsyncButton.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import FormField from '@/components/ui/FormField.vue'
import InlineAlert from '@/components/ui/InlineAlert.vue'
import { downloadICS } from '@/composables/useCalendar'
import { useToast } from '@/composables/useToast'
import { parseFormError } from '@/lib/formError'
import LessonTimeFields from './LessonTimeFields.vue'

const props = defineProps<{
  lesson: Lesson | null
  students: Student[]
  defaultDuration: number
  currencySymbol: string
}>()

const emit = defineEmits<{
  close: []
  refresh: []
  'open-reschedule': []
}>()

const toast = useToast()
const editForm = reactive({
  date: '', start_time: '', duration_hours: 1, status: '待上' as Lesson['status'], note: '',
})
const message = ref('')
const error = ref('')
const saving = ref(false)
const statusUpdating = ref<Lesson['status'] | null>(null)
const deleting = ref(false)
const confirmDeleteOpen = ref(false)
const busy = computed(() => saving.value || Boolean(statusUpdating.value) || deleting.value)

watch(() => props.lesson, (lesson) => {
  if (!lesson) return
  editForm.date = lesson.date
  editForm.start_time = lesson.start_time.slice(0, 5)
  editForm.duration_hours = lesson.duration_hours
  editForm.status = lesson.status
  editForm.note = lesson.note ?? ''
  message.value = ''
  error.value = ''
  confirmDeleteOpen.value = false
}, { immediate: true })

const studentName = computed(() => {
  if (!props.lesson) return ''
  return props.students.find(student => student.id === props.lesson?.student_id)?.name
    ?? `学生 #${props.lesson.student_id}`
})

function resetFeedback() {
  message.value = ''
  error.value = ''
}

async function updateStatus(status: Lesson['status']) {
  if (!props.lesson || busy.value) return
  resetFeedback()
  statusUpdating.value = status
  try {
    if (status === '请假') await lessonsApi.cancel(props.lesson.id, editForm.note || undefined)
    else if (status === '待上') await lessonsApi.restore(props.lesson.id)
    else await lessonsApi.update(props.lesson.id, { status })
    editForm.status = status
    message.value = `状态已更新为“${status}”`
    toast.show('课时状态已更新')
    emit('refresh')
  } catch (err) {
    error.value = parseFormError(err)
  } finally {
    statusUpdating.value = null
  }
}

async function updateLesson() {
  if (!props.lesson || busy.value) return
  resetFeedback()
  saving.value = true
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
    error.value = parseFormError(err)
  } finally {
    saving.value = false
  }
}

async function removeLesson() {
  if (!props.lesson || busy.value) return
  resetFeedback()
  deleting.value = true
  try {
    await lessonsApi.remove(props.lesson.id)
    toast.show('课时已删除')
    confirmDeleteOpen.value = false
    emit('refresh')
    emit('close')
  } catch (err) {
    error.value = parseFormError(err)
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <AppDialog
    :open="Boolean(lesson)"
    title="课时操作"
    description="更新课程状态、时间和备注"
    size="lg"
    :close-disabled="busy"
    @close="emit('close')"
  >
    <div v-if="lesson" class="space-y-5">
      <section class="rounded-2xl border border-white/35 bg-white/45 p-3.5 dark:border-white/10 dark:bg-white/5">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-sm font-semibold">{{ studentName }}</p>
            <p class="mt-1 text-xs text-[var(--text-dim)]">{{ lesson.date }} · {{ lesson.start_time.slice(0, 5) }} · {{ lesson.duration_hours }} 小时</p>
          </div>
          <span :class="['badge text-[11px]', lesson.status === '已完成' ? 'badge-success' : lesson.status === '请假' ? 'badge-warning' : lesson.status === '已调课' ? 'badge-muted' : 'badge-info']">
            {{ lesson.status }}
          </span>
        </div>
      </section>

      <section aria-labelledby="lesson-quick-actions">
        <h3 id="lesson-quick-actions" class="mb-2 text-xs font-semibold text-[var(--text-dim)]">快捷操作</h3>
        <div class="flex flex-wrap gap-2">
          <AsyncButton type="button" tone="ghost" size="sm" :pending="statusUpdating === '已完成'" :disabled="busy" pending-label="完成中…" @click="updateStatus('已完成')">完成</AsyncButton>
          <AsyncButton type="button" tone="ghost" size="sm" :pending="statusUpdating === '请假'" :disabled="busy" pending-label="请假中…" @click="updateStatus('请假')">请假</AsyncButton>
          <AsyncButton type="button" tone="ghost" size="sm" :pending="statusUpdating === '待上'" :disabled="busy" pending-label="恢复中…" @click="updateStatus('待上')">恢复</AsyncButton>
          <button type="button" class="btn-ghost btn-sm" :disabled="busy" @click="downloadICS(lesson, studentName)">加入日历</button>
          <button type="button" data-action="delete-lesson" class="btn-danger btn-sm" :disabled="busy" @click="confirmDeleteOpen = true">删除</button>
        </div>
      </section>

      <form data-form="lesson-edit" class="space-y-4 border-t border-white/30 pt-4 dark:border-white/10" @submit.prevent="updateLesson">
        <h3 class="text-sm font-semibold">编辑课时</h3>
        <LessonTimeFields
          v-model:date="editForm.date"
          v-model:start-time="editForm.start_time"
          v-model:duration-hours="editForm.duration_hours"
          id-prefix="edit-lesson"
        />
        <FormField for-id="edit-lesson-status" label="状态">
          <template #default="{ describedby }">
            <select id="edit-lesson-status" v-model="editForm.status" class="input" :disabled="busy" :aria-describedby="describedby || undefined">
              <option value="待上">待上</option><option value="已完成">已完成</option>
              <option value="请假">请假</option><option value="已调课">已调课</option>
            </select>
          </template>
        </FormField>
        <FormField for-id="edit-lesson-note" label="备注">
          <template #default="{ describedby }">
            <textarea id="edit-lesson-note" v-model="editForm.note" class="input min-h-20 resize-y" :disabled="busy" :aria-describedby="describedby || undefined" />
          </template>
        </FormField>
        <InlineAlert v-if="message" tone="success" :message="message" />
        <InlineAlert v-if="error" tone="error" :message="error" />
        <div class="flex flex-wrap gap-2">
          <AsyncButton data-action="save-lesson" :pending="saving" :disabled="busy" pending-label="保存中…">保存修改</AsyncButton>
          <button type="button" class="btn-ghost" :disabled="busy" @click="emit('open-reschedule')">调课 →</button>
        </div>
      </form>
    </div>
  </AppDialog>

  <ConfirmDialog
    v-model:open="confirmDeleteOpen"
    title="删除这节课程？"
    :description="`${studentName} · ${lesson?.date ?? ''}，删除后不可撤销。`"
    confirm-label="删除课程"
    :pending="deleting"
    pending-label="删除中…"
    @confirm="removeLesson"
  />
</template>
