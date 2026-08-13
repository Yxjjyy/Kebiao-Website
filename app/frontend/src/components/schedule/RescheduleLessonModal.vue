<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { lessonsApi } from '@/api/lessons'
import type { Lesson } from '@/api/types'
import AsyncButton from '@/components/ui/AsyncButton.vue'
import AppDialog from '@/components/ui/AppDialog.vue'
import FormField from '@/components/ui/FormField.vue'
import InlineAlert from '@/components/ui/InlineAlert.vue'
import { useToast } from '@/composables/useToast'
import { parseFormError } from '@/lib/formError'
import LessonTimeFields from './LessonTimeFields.vue'

const props = defineProps<{
  lesson: Lesson | null
  defaultDuration: number
  currencySymbol: string
}>()

const emit = defineEmits<{
  close: []
  refresh: []
}>()

const toast = useToast()
const form = reactive({ new_date: '', new_start_time: '', new_duration_hours: 1, note: '' })
const error = ref('')
const submitting = ref(false)

watch(() => props.lesson, (lesson) => {
  if (!lesson) return
  form.new_date = lesson.date
  form.new_start_time = lesson.start_time.slice(0, 5)
  form.new_duration_hours = lesson.duration_hours
  form.note = lesson.note ?? ''
  error.value = ''
}, { immediate: true })

async function submit() {
  if (!props.lesson || submitting.value) return
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
    error.value = parseFormError(err)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppDialog
    :open="Boolean(lesson)"
    title="调课"
    description="核对原课程后设置新的上课安排"
    size="lg"
    :close-disabled="submitting"
    @close="emit('close')"
  >
    <form v-if="lesson" class="space-y-4" @submit.prevent="submit">
      <div class="grid gap-3 md:grid-cols-2">
        <section class="rounded-2xl border border-white/35 bg-white/35 px-3.5 py-3 dark:border-white/10 dark:bg-white/5">
          <p class="text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--text-dim)]">原课程</p>
          <p class="mt-2 text-sm font-semibold">{{ lesson.student?.name ?? '未命名学生' }}</p>
          <p class="mt-1 text-xs text-[var(--text-dim)]">{{ lesson.date }} · {{ lesson.start_time.slice(0, 5) }} · {{ lesson.duration_hours }} 小时</p>
        </section>
        <section class="rounded-2xl border border-[var(--accent)]/20 bg-[var(--accent)]/5 px-3.5 py-3">
          <p class="text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--accent)]">目标安排</p>
          <p class="mt-2 text-sm font-semibold">{{ form.new_date || '待选择日期' }}</p>
          <p class="mt-1 text-xs text-[var(--text-dim)]">{{ form.new_start_time || '待选择时间' }} · {{ form.new_duration_hours }} 小时</p>
        </section>
      </div>

      <LessonTimeFields
        v-model:date="form.new_date"
        v-model:start-time="form.new_start_time"
        v-model:duration-hours="form.new_duration_hours"
        date-label="新日期"
        time-label="新时间"
        duration-label="新课时"
        id-prefix="reschedule-lesson"
        :disabled="submitting"
      />

      <FormField for-id="reschedule-lesson-note" label="备注" hint="可选，说明本次调课原因">
        <template #default="{ describedby }">
          <textarea id="reschedule-lesson-note" v-model="form.note" class="input min-h-20 resize-y" :aria-describedby="describedby || undefined" />
        </template>
      </FormField>

      <InlineAlert v-if="error" tone="error" :message="error" />
      <div class="flex justify-end">
        <AsyncButton :pending="submitting" pending-label="提交中…">确认调课</AsyncButton>
      </div>
    </form>
  </AppDialog>
</template>
