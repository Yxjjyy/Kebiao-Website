<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { lessonsApi } from '@/api/lessons'
import type { Student } from '@/api/types'
import AsyncButton from '@/components/ui/AsyncButton.vue'
import AppDialog from '@/components/ui/AppDialog.vue'
import FormField from '@/components/ui/FormField.vue'
import InlineAlert from '@/components/ui/InlineAlert.vue'
import { useToast } from '@/composables/useToast'
import { formatCurrency } from '@/lib/format'
import { parseFormError } from '@/lib/formError'
import LessonTimeFields from './LessonTimeFields.vue'

const props = defineProps<{
  students: Student[]
  defaultDuration: number
  currencySymbol: string
  quickCreate: { date: string; start_time: string } | null
}>()

const emit = defineEmits<{
  close: []
  refresh: []
}>()

const toast = useToast()
const form = reactive({
  student_id: 0,
  date: new Date().toISOString().slice(0, 10),
  start_time: '10:00',
  duration_hours: 1,
  note: '',
})
const error = ref('')
const submitting = ref(false)

watch(() => props.defaultDuration, value => { form.duration_hours = value }, { immediate: true })
watch(() => props.quickCreate, (value) => {
  if (!value) return
  form.date = value.date
  form.start_time = value.start_time
}, { immediate: true })

const selectedStudent = computed(() => props.students.find(student => student.id === form.student_id))
const estimate = computed(() => formatCurrency(
  (selectedStudent.value?.hourly_rate ?? 0) * form.duration_hours,
  props.currencySymbol,
))

async function createLesson() {
  if (submitting.value) return
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
    error.value = parseFormError(err)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppDialog
    :open="true"
    title="新增临时课"
    description="一次性补课或临时新增"
    :close-disabled="submitting"
    @close="emit('close')"
  >
    <form class="space-y-4" @submit.prevent="createLesson">
      <FormField for-id="create-lesson-student" label="学生" required>
        <template #default="{ describedby }">
          <select
            id="create-lesson-student"
            v-model.number="form.student_id"
            class="input"
            required
            :aria-describedby="describedby || undefined"
          >
            <option disabled value="0">请选择学生</option>
            <option v-for="student in students" :key="student.id" :value="student.id">
              {{ student.name }}
            </option>
          </select>
        </template>
      </FormField>

      <div v-if="selectedStudent" class="rounded-2xl border border-white/35 bg-white/35 px-3.5 py-3 text-xs dark:border-white/10 dark:bg-white/5">
        <div class="font-semibold text-[var(--text)]">{{ selectedStudent.name }}</div>
        <div class="mt-1 text-[var(--text-dim)]">当前课时预估 {{ estimate }}</div>
      </div>

      <LessonTimeFields
        v-model:date="form.date"
        v-model:start-time="form.start_time"
        v-model:duration-hours="form.duration_hours"
        id-prefix="create-lesson"
      />

      <FormField for-id="create-lesson-note" label="备注" hint="可选，记录补课原因或课堂重点">
        <template #default="{ describedby }">
          <textarea id="create-lesson-note" v-model="form.note" class="input min-h-20 resize-y" :aria-describedby="describedby || undefined" />
        </template>
      </FormField>

      <InlineAlert v-if="error" tone="error" :message="error" />
      <AsyncButton
        data-action="create-lesson"
        class="w-full"
        :pending="submitting"
        pending-label="创建中…"
      >
        创建课时
      </AsyncButton>
    </form>
  </AppDialog>
</template>
